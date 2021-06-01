import logging
import traceback

from openforms.submissions.constants import AppointmentStatuses
from openforms.submissions.models import Submission

from .exceptions import AppointmentFailed

logger = logging.getLogger(__name__)


def create_appointment(submission_id: int):
    submission = Submission.objects.get(id=submission_id)
    # figure out which registry and backend to use from the model field used
    form = submission.form
    backend = form.appointment_backend
    registry = form._meta.get_field("appointment_backend").registry

    if not backend:
        logger.info("Form %s has no appointment plugin configured, aborting", form)
        return

    logger.debug("Looking up plugin with unique identifier '%s'", backend)
    plugin = registry[backend]

    logger.debug("De-serializing the plugin configuration options")
    options_serializer = plugin.configuration_options(
        data=form.appointment_backend_options
    )
    options_serializer.is_valid(raise_exception=True)

    logger.debug("Invoking the '%r' plugin callback", plugin.callback)
    try:
        result = plugin.callback(submission, options_serializer.validated_data)
    except AppointmentFailed:
        formatted_tb = traceback.format_exc()
        status = AppointmentStatuses.failed
        result_data = {"traceback": formatted_tb}
    else:
        status = AppointmentStatuses.success
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

    submission.appointment_status = status
    submission.appointment_result = result_data
    submission.save(update_fields=["appointment_status", "appointment_result"])

    return
