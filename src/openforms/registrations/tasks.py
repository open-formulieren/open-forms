import logging
import traceback
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.utils import timezone

from celery_once import QueueOnce

from openforms.celery import app
from openforms.logging import logevent
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission

from .exceptions import RegistrationFailed

logger = logging.getLogger(__name__)


@app.task(
    base=QueueOnce,
    ignore_result=False,
    once={"graceful": True},  # do not spam error monitoring
)
def register_submission(submission_id: int) -> Optional[dict]:
    """
    Attempt to register the submission with the configured backend.

    Note that there are different triggers that can kick off this task:

    * form submission :func:`openforms.submissions.tasks.on_completion` flow
    * celery beat retry flow
    * admin action to retry the submission

    We should only allow a single registration attempt to run at a given time for a
    given submission. This is achieved through the :class:`QueueOnce` task base class
    from celery-once. While the task is already scheduled, subsequent schedule requests
    will not schedule the task _again_ to celery.

    Submission registration is only executed for "completed" forms, and is delegated
    to the underlying registration backend (if set).
    """
    submission = Submission.objects.get(id=submission_id)

    logger.debug("Register submission '%s'", submission)

    if submission.registration_status == RegistrationStatuses.success:
        # if it's already succesfully registered, do not overwrite that.
        return

    logevent.registration_start(submission)

    if not submission.completed_on:
        e = RegistrationFailed("Submission should be completed first")
        logevent.registration_failure(submission, e)
        raise e

    submission.last_register_date = timezone.now()
    submission.registration_status = RegistrationStatuses.in_progress
    submission.save(update_fields=["last_register_date", "registration_status"])

    # figure out which registry and backend to use from the model field used
    form = submission.form
    backend = form.registration_backend
    registry = form._meta.get_field("registration_backend").registry

    if not backend:
        logger.info("Form %s has no registration plugin configured, aborting", form)
        submission.save_registration_status(RegistrationStatuses.success, None)
        logevent.registration_skip(submission)
        return

    logger.debug("Looking up plugin with unique identifier '%s'", backend)
    plugin = registry[backend]

    logger.debug("De-serializing the plugin configuration options")
    options_serializer = plugin.configuration_options(
        data=form.registration_backend_options
    )
    try:
        options_serializer.is_valid(raise_exception=True)
    except Exception as e:
        submission.save_registration_status(
            RegistrationStatuses.failed, {"traceback": traceback.format_exc()}
        )
        logevent.registration_failure(submission, e, plugin)
        raise

    logger.debug("Invoking the '%r' plugin callback", plugin)
    try:
        result = plugin.register_submission(
            submission, options_serializer.validated_data
        )
    # downstream tasks can still execute, so we return rather than failing.
    except RegistrationFailed as e:
        submission.save_registration_status(
            RegistrationStatuses.failed, {"traceback": traceback.format_exc()}
        )
        logevent.registration_failure(submission, e, plugin)
        return
    # unexpected exceptions should fail the entire chain and show up in error monitoring
    except Exception as e:
        submission.save_registration_status(
            RegistrationStatuses.failed, {"traceback": traceback.format_exc()}
        )
        logevent.registration_failure(submission, e, plugin)
        raise
    else:
        submission.save_registration_status(RegistrationStatuses.success, result)
        logevent.registration_success(submission, plugin)


@app.task(ignore_result=True)
def resend_submissions():
    # TODO: refactor to retry_completion_chain
    resend_time_limit = timezone.now() - timedelta(
        hours=settings.CELERY_BEAT_RESEND_SUBMISSIONS_TIME_LIMIT
    )
    for submission in Submission.objects.filter(
        registration_status=RegistrationStatuses.failed,
        completed_on__gte=resend_time_limit,
    ):
        logger.debug("Resend submission for registration '%s'", submission)
        register_submission.delay(submission.id)
