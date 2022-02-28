import base64
import io
import logging
import re
from datetime import datetime
from typing import List, Optional

from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

import elasticapm
import qrcode

from openforms.forms.models import Form, FormStep
from openforms.logging import logevent
from openforms.submissions.models import Submission

from .base import AppointmentClient, AppointmentLocation, AppointmentProduct
from .constants import AppointmentDetailsStatus
from .exceptions import AppointmentCreateFailed, AppointmentDeleteFailed
from .models import AppointmentInfo, AppointmentsConfig
from .service import AppointmentRegistrationFailed

logger = logging.getLogger()


def get_client():
    config_path = AppointmentsConfig.get_solo().config_path
    if not config_path:
        raise ValueError("No config_path is specified in AppointmentsConfig")
    config_class = import_string(config_path)
    client = config_class.get_solo().get_client()
    return client


def get_missing_fields_labels(
    appointment_data: dict, missing_fields_keys: List[str]
) -> List[str]:
    labels = []
    for key in missing_fields_keys:
        if label := appointment_data.get(key, {}).get("label"):
            labels.append(label)
        else:
            labels.append(key)
    return sorted(labels)


def get_formatted_phone_number(phone_number: Optional[str]) -> Optional[str]:
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

    product = AppointmentProduct(
        identifier=appointment_data["productIDAndName"]["value"]["identifier"],
        name=appointment_data["productIDAndName"]["value"]["name"],
    )
    location = AppointmentLocation(
        identifier=appointment_data["locationIDAndName"]["value"]["identifier"],
        name=appointment_data["locationIDAndName"]["value"]["name"],
    )
    appointment_client = AppointmentClient(
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

    client = get_client()
    try:
        logevent.appointment_register_start(submission, client)
        appointment_id = client.create_appointment(
            [product], location, start_at, appointment_client
        )
        appointment_info = AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.success,
            appointment_id=appointment_id,
            submission=submission,
            start_time=start_at,
        )
        logevent.appointment_register_success(appointment_info, client)
    except AppointmentCreateFailed as e:
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
        logevent.appointment_register_failure(appointment_info, client, e)
        raise AppointmentRegistrationFailed("Unable to create appointment") from e

    cancel_previous_submission_appointment(submission)


@elasticapm.capture_span(span_type="app.appointments.cancel")
def cancel_previous_submission_appointment(submission: Submission) -> None:
    """
    Given a submission, check if there's a previous appointment to cancel.
    """
    if not submission.previous_submission:
        logger.debug(
            "Submission %s has no known previous appointment to cancel", submission.uuid
        )
        return

    # check if there's anything to cancel at all
    try:
        appointment_info = submission.previous_submission.appointment_info
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

    client = get_client()

    logger.debug(
        "Attempting to cancel appointment %s of submission %s",
        appointment_info.appointment_id,
        submission.uuid,
    )
    logevent.appointment_cancel_start(appointment_info, client)

    try:
        delete_appointment_for_submission(submission.previous_submission)
    except AppointmentDeleteFailed:
        logger.warning(
            "Deleting the appointment %s of submission %s failed",
            appointment_info.appointment_id,
            submission.uuid,
        )


@elasticapm.capture_span(span_type="app.appointments.delete")
def delete_appointment_for_submission(submission: Submission, client=None) -> None:
    """
    Delete/cancels the appointment for a given submission.

    :raises CancelAppointmentFailed: if the plugin errored or there was no relevant
      appointment information.
    """
    client = client or get_client()
    try:
        appointment_info = submission.appointment_info
    except AppointmentInfo.DoesNotExist:
        logger.info(
            "Submission %s had no recorded appointment information, aborting deletion.",
            submission.uuid,
        )
        return

    try:
        client.delete_appointment(appointment_info.appointment_id)
        appointment_info.cancel()
    except AppointmentDeleteFailed as e:
        logevent.appointment_cancel_failure(appointment_info, client, e)
        raise

    logevent.appointment_cancel_success(appointment_info, client)


def create_base64_qrcode(text):
    img = qrcode.make(text)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("ascii")


def find_first_appointment_step(form: Form) -> Optional[FormStep]:
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
