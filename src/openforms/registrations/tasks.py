import logging
import traceback
from typing import Optional

from django.db import transaction

from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models import Submission, SubmissionReport

from ..celery import app
from .exceptions import RegistrationFailed

logger = logging.getLogger(__name__)


@app.task()
@transaction.atomic()
def register_submission(submission_id: int) -> Optional[dict]:
    submission = Submission.objects.get(id=submission_id)
    # figure out which registry and backend to use from the model field used
    form = submission.form
    backend = form.registration_backend
    registry = form._meta.get_field("registration_backend").registry

    if not backend:
        logger.info("Form %s has no registration plugin configured, aborting", form)
        return

    logger.debug("Looking up plugin with unique identifier '%s'", backend)
    plugin = registry[backend]

    logger.debug("De-serializing the plugin configuration options")
    options_serializer = plugin.configuration_options(
        data=form.registration_backend_options
    )
    options_serializer.is_valid(raise_exception=True)

    logger.debug("Invoking the '%r' plugin callback", plugin.callback)
    try:
        result = plugin.callback(submission, options_serializer.validated_data)
    except RegistrationFailed:
        formatted_tb = traceback.format_exc()
        status = RegistrationStatuses.failed
        result_data = {"traceback": formatted_tb}
    else:
        status = RegistrationStatuses.success
        if plugin.backend_feedback_serializer:
            logger.debug(
                "Serializing the callback result with '%r'",
                plugin.backend_feedback_serializer,
            )
            result_serializer = plugin.backend_feedback_serializer(instance=result)
            result_data = result_serializer.data
        else:
            logger.debug(
                "No result serializer specified, assuming raw result can be serialized as JSON"
            )
            result_data = result

    submission.registration_status = status
    submission.registration_result = result_data
    submission.save(update_fields=["registration_status", "registration_result"])


@app.task(bind=True)
def generate_submission_report(task, submission_report_id: int) -> None:
    submission_report = SubmissionReport.objects.get(id=submission_report_id)
    submission_report.generate_submission_report_pdf()

    submission_report.task_id = task.request.id
    submission_report.save()
