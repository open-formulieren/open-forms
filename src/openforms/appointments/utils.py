import base64
import io
from datetime import datetime

from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

import qrcode

from openforms.submissions.models import Submission

from .base import AppointmentClient, AppointmentLocation, AppointmentProduct
from .constants import AppointmentDetailsStatus
from .exceptions import AppointmentCreateFailed
from .models import AppointmentInfo, AppointmentsConfig
from .service import AppointmentRegistrationFailed


def get_client():
    config_path = AppointmentsConfig.get_solo().config_path
    if not config_path:
        raise ValueError("No config_path is specified in AppointmentsConfig")
    config_class = import_string(config_path)
    client = config_class.get_solo().get_client()
    return client


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
        "productID",
        "locationID",
        "appStartTime",
        "clientLastName",
        "clientDateOfBirth",
    ]

    absent_or_empty_information = []

    for key in expected_information:
        # there is a non-empty value, continue - this is good
        if appointment_data.get(key):
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
        # TODO: resolve the keys back to the human readable form field labels
        error_information = _(
            "The following appoinment fields should be filled out: {fields}"
        ).format(fields=", ".join(sorted(absent_or_empty_information)))
        AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.missing_info,
            error_information=error_information,
            submission=submission,
        )
        raise AppointmentRegistrationFailed(
            "No registration attempted because of incomplete information. ",
            should_retry=False,
        )

    product = AppointmentProduct(identifier=str(appointment_data["productID"]), name="")
    location = AppointmentLocation(identifier=appointment_data["locationID"], name="")
    appointment_client = AppointmentClient(
        last_name=appointment_data["clientLastName"],
        birthdate=datetime.strptime(
            appointment_data["clientDateOfBirth"], "%Y-%m-%d"
        ).date(),
    )
    start_at = datetime.strptime(
        appointment_data["appStartTime"], "%Y-%m-%dT%H:%M:%S%z"
    )

    try:
        client = get_client()
        appointment_id = client.create_appointment(
            [product], location, start_at, appointment_client
        )
        AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.success,
            appointment_id=appointment_id,
            submission=submission,
            start_time=start_at,
        )
    except AppointmentCreateFailed as e:
        AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.failed,
            error_information="Failed to make appointment",
            submission=submission,
        )
        raise AppointmentRegistrationFailed(
            "Unable to create appointment", should_retry=True
        ) from e


def create_base64_qrcode(text):
    img = qrcode.make(text)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("ascii")
