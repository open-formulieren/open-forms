import logging
import traceback
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.utils import timezone

from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission
from openforms.utils.celery import maybe_retry_in_workflow

from ..celery import app
from .exceptions import RegistrationFailed

logger = logging.getLogger(__name__)


@maybe_retry_in_workflow(
    timeout=10,
    retry_for=(RegistrationFailed,),
)
@app.task(
    autoretry_for=(RegistrationFailed,),
    max_retries=settings.SUBMISSION_REGISTRATION_MAX_RETRIES,
)
def register_submission(submission_id: int) -> Optional[dict]:
    submission = Submission.objects.get(id=submission_id)

    if submission.registration_status == RegistrationStatuses.success:
        # It's possible for two instances of this task to run for the same submission
        #  (eg.  A user runs the admin action and the celery beat task runs)
        # so if the submission has already succeed we just return
        return

    if not submission.completed_on:
        raise RegistrationFailed("Submission should be completed first")

    submission.last_register_date = timezone.now()
    submission.registration_status = RegistrationStatuses.in_progress
    submission.save(update_fields=["last_register_date", "registration_status"])
    # figure out which registry and backend to use from the model field used
    form = submission.form
    backend = form.registration_backend
    registry = form._meta.get_field("registration_backend").registry

    if not backend:
        logger.info("Form %s has no registration plugin configured, aborting", form)
        submission.registration_status = RegistrationStatuses.success
        submission.save(update_fields=["registration_status"])
        return

    logger.debug("Looking up plugin with unique identifier '%s'", backend)
    plugin = registry[backend]

    logger.debug("De-serializing the plugin configuration options")
    options_serializer = plugin.configuration_options(
        data=form.registration_backend_options
    )
    options_serializer.is_valid(raise_exception=True)

    logger.debug("Invoking the '%r' plugin callback", plugin)
    try:
        result = plugin.register_submission(
            submission, options_serializer.validated_data
        )
    except RegistrationFailed:
        formatted_tb = traceback.format_exc()
        submission.registration_status = RegistrationStatuses.failed
        submission.registration_result = {"traceback": formatted_tb}
        submission.save(
            update_fields=[
                "registration_status",
                "registration_result",
            ]
        )
        raise
    else:
        status = RegistrationStatuses.success

    submission.registration_status = status
    submission.registration_result = result
    submission.save(
        update_fields=[
            "registration_status",
            "registration_result",
        ]
    )


@app.task(ignore_result=True)
def resend_submissions():
    resend_time_limit = timezone.now() - timedelta(
        hours=settings.CELERY_BEAT_RESEND_SUBMISSIONS_TIME_LIMIT
    )
    for submission in Submission.objects.filter(
        registration_status=RegistrationStatuses.failed,
        completed_on__gte=resend_time_limit,
    ):
        register_submission.delay(submission.id)
