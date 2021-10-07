import logging
import traceback
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.utils import timezone

from openforms.celery import app
from openforms.logging import logevent
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission

from .exceptions import RegistrationFailed

logger = logging.getLogger(__name__)


@app.task()
def register_submission(submission_id: int) -> Optional[dict]:
    submission = Submission.objects.get(id=submission_id)

    logger.debug("Register submission '%s'", submission)

    if submission.registration_status == RegistrationStatuses.success:
        # It's possible for two instances of this task to run for the same submission
        #  (eg.  A user runs the admin action and the celery beat task runs)
        # so if the submission has already succeed we just return
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
    resend_time_limit = timezone.now() - timedelta(
        hours=settings.CELERY_BEAT_RESEND_SUBMISSIONS_TIME_LIMIT
    )
    for submission in Submission.objects.filter(
        registration_status=RegistrationStatuses.failed,
        completed_on__gte=resend_time_limit,
    ):
        logger.debug("Resend submission for registration '%s'", submission)
        register_submission.delay(submission.id)
