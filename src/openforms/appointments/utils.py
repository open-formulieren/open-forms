import base64
import io
import logging
import re
import warnings
from datetime import datetime

from django.utils.translation import gettext_lazy as _

import elasticapm
import qrcode

from openforms.forms.models import Form, FormStep
from openforms.logging import logevent
from openforms.submissions.models import Submission

from .base import BasePlugin, Customer, Location, Product
from .constants import AppointmentDetailsStatus
from .exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentRegistrationFailed,
)
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


def get_missing_fields_labels(
    appointment_data: dict, missing_fields_keys: list[str]
) -> list[str]:
    labels = []
    for key in missing_fields_keys:
        if label := appointment_data.get(key, {}).get("label"):
            labels.append(label)
        else:
            labels.append(key)
    return sorted(labels)


def get_formatted_phone_number(phone_number: str | None) -> str | None:
    """
    Remove any character that isn't numeric or a space, +, or - character
    and return max 16 characters
    """
    if not phone_number:
        return

    phone_number = re.sub("[^- +0-9]", "", phone_number)

    return phone_number[:16]


@elasticapm.capture_span(span_type="app.appointments.book")
def book_appointment_for_submission(submission: Submission) -> None:
    warnings.warn(
        "Old-style appointments are deprecated, please update the form to use "
        "the reworked appointments.",
        DeprecationWarning,
    )
    try:
        # Delete the previous appointment info if there is one since
        #   since a new one will be created
        # This function will be called multiple times on a failure so
        #   this is the case a previous appointment_info may exist
        submission.appointment_info.delete()
    except AppointmentInfo.DoesNotExist:
        pass

    appointment_data = submission.get_merged_appointment_data()

    expected_information = [
        "productIDAndName",
        "locationIDAndName",
        "appStartTime",
        "clientLastName",
        "clientDateOfBirth",
    ]

    absent_or_empty_information = []

    for key in expected_information:
        # there is a non-empty value, continue - this is good
        if appointment_data.get(key, {}).get("value"):
            continue
        absent_or_empty_information.append(key)

    # Submission was never intended to make an appointment so just return
    if set(absent_or_empty_information) == set(expected_information):
        return

    # Partially filled out form (or appointment fields are present in the form and not
    # filled at all). Note that the "contract" states an exception gets raised here
    # which aborts the celery chain execution so that the end-user can be shown the
    # error information.
    if absent_or_empty_information:
        # Incomplete information to make an appointment
        logevent.appointment_register_skip(submission)
        missing_fields_labels = get_missing_fields_labels(
            appointment_data, absent_or_empty_information
        )
        error_information = _(
            "The following appointment fields should be filled out: {fields}"
        ).format(fields=", ".join(missing_fields_labels))
        AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.missing_info,
            error_information=error_information,
            submission=submission,
        )
        raise AppointmentRegistrationFailed(
            "No registration attempted because of incomplete information. "
        )

    product = Product(
        identifier=appointment_data["productIDAndName"]["value"]["identifier"],
        name=appointment_data["productIDAndName"]["value"]["name"],
    )
    location = Location(
        identifier=appointment_data["locationIDAndName"]["value"]["identifier"],
        name=appointment_data["locationIDAndName"]["value"]["name"],
    )
    appointment_client = Customer(
        last_name=appointment_data["clientLastName"]["value"],
        birthdate=datetime.strptime(
            appointment_data["clientDateOfBirth"]["value"], "%Y-%m-%d"
        ).date(),
        phonenumber=get_formatted_phone_number(
            appointment_data.get("clientPhoneNumber", {}).get("value")
        ),
    )
    start_at = datetime.strptime(
        appointment_data["appStartTime"]["value"], "%Y-%m-%dT%H:%M:%S%z"
    )

    plugin = get_plugin()
    try:
        logevent.appointment_register_start(submission, plugin)
        appointment_id = plugin.create_appointment(
            [product], location, start_at, appointment_client
        )
        appointment_info = AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.success,
            appointment_id=appointment_id,
            submission=submission,
            start_time=start_at,
        )
        logevent.appointment_register_success(appointment_info, plugin)
    except AppointmentCreateFailed as e:
        logger.error("Appointment creation failed", exc_info=e)
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
        logevent.appointment_register_failure(appointment_info, plugin, e)
        raise AppointmentRegistrationFailed("Unable to create appointment") from e

    cancel_previous_submission_appointment(submission)


@elasticapm.capture_span(span_type="app.appointments.cancel")
def cancel_previous_submission_appointment(submission: Submission) -> None:
    """
    Given a submission, check if there's a previous appointment to cancel.
    """
    if not (previous_submission := submission.previous_submission):
        logger.debug(
            "Submission %s has no known previous appointment to cancel", submission.uuid
        )
        return

    # check if there's anything to cancel at all
    try:
        appointment_info = previous_submission.appointment_info
    except AppointmentInfo.DoesNotExist:
        logger.debug(
            "Submission %s has no known previous appointment to cancel", submission.uuid
        )
        return

    if (
        appointment_info.status != AppointmentDetailsStatus.success
        or not appointment_info.appointment_id
    ):
        logger.debug(
            "Submission %s has no known previous appointment to cancel", submission.uuid
        )
        return

    # check for new-style appointments
    appointment = Appointment.objects.filter(submission=previous_submission).first()
    plugin = get_plugin(plugin=appointment.plugin if appointment else "")

    logger.debug(
        "Attempting to cancel appointment %s of submission %s",
        appointment_info.appointment_id,
        submission.uuid,
    )
    logevent.appointment_cancel_start(appointment_info, plugin)

    try:
        delete_appointment_for_submission(previous_submission, plugin=plugin)
    except AppointmentDeleteFailed:
        logger.warning(
            "Deleting the appointment %s of submission %s failed",
            appointment_info.appointment_id,
            submission.uuid,
        )


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


def find_first_appointment_step(form: Form) -> FormStep | None:
    """
    Find the first step in a form dealing with appointments.

    This looks at the component configuration for each step and detects if a component
    is holding appointment-related meta-information. If no such step is found, ``None``
    is returned.
    """
    for form_step in form.formstep_set.select_related("form_definition"):
        for component in form_step.iter_components(recursive=True):
            if "appointments" not in component:
                continue

            if component["appointments"].get("showProducts"):
                return form_step

    # no component in any form step found that satisfies
    return None


def get_confirmation_mail_suffix(submission: Submission) -> str:
    """
    Determine the suffix, if appropriate for the subject of the confirmation mail.

    If this submission is related to an appointment and previous submission,
    append an "updated" marker to the subject (see #680).
    """
    # if there's no related previous submission, it cannot be an update
    if not submission.previous_submission_id:
        return ""

    # if there's no appointment info attached to the previous submission, it cannot be
    # an update
    try:
        appointment_info = submission.previous_submission.appointment_info
    except AppointmentInfo.DoesNotExist:
        return ""

    # if the previous appointment was not cancelled, it cannot be an update
    # TODO: what to do when we did succesfully create a new appointment, but the old
    # one deletion failed? there are now two appointments open.
    # submission.appointment_info.status == AppointmentDetailsStatus.success and
    # submission.previous_submission.appointment_info.status == AppointmentDetailsStatus.success
    if appointment_info.status != AppointmentDetailsStatus.cancelled:
        return ""

    return _("(updated)")


def get_appointment(submission: Submission) -> Appointment | None:
    if not submission.form.is_appointment:
        return None
    appointment: Appointment | None = getattr(submission, "appointment", None)
    return appointment
