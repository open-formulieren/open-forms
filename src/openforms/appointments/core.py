"""
Core implementation of the generic API.

This module is the follow-up to the bulk of functionality in utils.py, which is doing
way too much but can't be easily refactored without breaking existing functionality.
"""

from django.utils.translation import gettext_lazy as _

import elasticapm
import structlog
from opentelemetry import trace

from openforms.logging import logevent
from openforms.submissions.models import Submission

from .base import BasePlugin, CustomerDetails, Location, Product
from .constants import AppointmentDetailsStatus
from .exceptions import (
    AppointmentCreateFailed,
    AppointmentRegistrationFailed,
    NoAppointmentForm,
)
from .models import Appointment, AppointmentInfo
from .registry import register

__all__ = ["book_for_submission"]

logger = structlog.stdlib.get_logger(__name__)
tracer = trace.get_tracer("openforms.appointments.core")


def _get_plugin(appointment: Appointment) -> BasePlugin:
    plugin = register[appointment.plugin]
    assert isinstance(plugin, BasePlugin)
    return plugin


def book(appointment: Appointment, remarks: str = "") -> str:
    """
    Book the appointment from the data in the model instance.
    """
    plugin = _get_plugin(appointment)

    # convert DB data into domain objects
    products = [
        Product(identifier=ap.product_id, amount=ap.amount, name="")
        for ap in appointment.products.all()
    ]
    location = Location(identifier=appointment.location, name="")
    normalized_data = plugin.normalize_contact_details(appointment.contact_details)
    customer = CustomerDetails(details=normalized_data)

    logevent.appointment_register_start(appointment.submission, plugin)
    appointment_id = plugin.create_appointment(
        products,
        location,
        appointment.datetime,
        customer,
        remarks=remarks,
    )
    appointment_info = AppointmentInfo.objects.create(
        status=AppointmentDetailsStatus.success,
        appointment_id=appointment_id,
        submission=appointment.submission,
        start_time=appointment.datetime,
    )
    logevent.appointment_register_success(appointment_info, plugin)
    return appointment_id


@tracer.start_as_current_span(
    name="book-for-submission",
    attributes={
        "span.type": "app",
        "span.subtype": "appointments",
        "span.action": "book_for_submission",
    },
)
@elasticapm.capture_span(span_type="app.appointments.book_for_submission")
def book_for_submission(submission: Submission) -> str:
    """
    Given a submission instance, check if an appointment needs to be booked.

    This flow is aborted when:

    * The form is not marked as appointment form, which flags the 'new-style'
      appointments.
    * There is no related :class:`Appointment` instance - this is an unexpected error.
      It could be caused by an existing form being changed into an appointment form with
      old data.
    """
    if not submission.form.is_appointment:
        raise NoAppointmentForm("Not an appointment form")

    try:
        appointment = submission.appointment
    except Appointment.DoesNotExist:
        logevent.appointment_register_skip(submission)
        raise AppointmentRegistrationFailed(
            "No registration attempted - there is no appointment data available."
        )

    assert isinstance(appointment, Appointment)
    # Delete the previous appointment info if there is one since a new one will be
    # created anyway.
    AppointmentInfo.objects.filter(submission=submission).delete()

    try:
        appointment_id = book(appointment)
    except AppointmentCreateFailed as exc:
        plugin = _get_plugin(appointment)
        logger.error(
            "appointment_register_failure",
            plugin=plugin,
            submission_uuid=str(submission.uuid),
            exc_info=exc,
        )
        # This is displayed to the end-user!
        error_information = _(
            "A technical error occurred while we tried to book your appointment. "
            "Please verify if all the data is correct or try again later."
        )
        appointment_info = AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.failed,
            error_information=error_information,
            submission=submission,
        )
        logevent.appointment_register_failure(appointment_info, plugin, exc)
        raise AppointmentRegistrationFailed("Unable to create appointment") from exc

    return appointment_id
