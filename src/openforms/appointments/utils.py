import base64
import io
import logging
import re

import elasticapm
import qrcode

from openforms.logging import logevent
from openforms.submissions.models import Submission

from .base import BasePlugin
from .exceptions import AppointmentDeleteFailed
from .models import Appointment, AppointmentInfo, AppointmentsConfig
from .registry import register

logger = logging.getLogger()


def get_plugin(plugin: str = "") -> BasePlugin:
    """returns plugin selected in AppointmentsConfig"""
    if not plugin:
        config = AppointmentsConfig.get_solo()
        if not (plugin := config.plugin):
            raise ValueError("No plugin is specified in AppointmentsConfig")
    return register[plugin]


def get_formatted_phone_number(phone_number: str | None) -> str | None:
    """
    Remove any character that isn't numeric or a space, +, or - character
    and return max 16 characters
    """
    if not phone_number:
        return

    phone_number = re.sub("[^- +0-9]", "", phone_number)

    return phone_number[:16]


@elasticapm.capture_span(span_type="app.appointments.delete")
def delete_appointment_for_submission(submission: Submission, plugin=None) -> None:
    """
    Delete/cancels the appointment for a given submission.

    :raises CancelAppointmentFailed: if the plugin errored or there was no relevant
      appointment information.
    """
    plugin = plugin or get_plugin()
    try:
        appointment_info = submission.appointment_info
    except AppointmentInfo.DoesNotExist:
        logger.info(
            "Submission %s had no recorded appointment information, aborting deletion.",
            submission.uuid,
        )
        return

    try:
        plugin.delete_appointment(appointment_info.appointment_id)
        appointment_info.cancel()
    except AppointmentDeleteFailed as e:
        logevent.appointment_cancel_failure(appointment_info, plugin, e)
        raise

    logevent.appointment_cancel_success(appointment_info, plugin)


def create_base64_qrcode(text):
    img = qrcode.make(text)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("ascii")


def get_appointment(submission: Submission) -> Appointment | None:
    if not submission.form.is_appointment:
        return None
    appointment: Appointment | None = getattr(submission, "appointment", None)
    return appointment
