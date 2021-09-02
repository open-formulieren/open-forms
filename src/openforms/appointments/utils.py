import base64
import io
from datetime import datetime

from django.utils.module_loading import import_string

import qrcode

from openforms.submissions.models import Submission

from .base import AppointmentClient, AppointmentLocation, AppointmentProduct
from .constants import AppointmentDetailsStatus
from .exceptions import AppointmentCreateFailed
from .models import AppointmentInfo, AppointmentsConfig


def get_client():
    config_path = AppointmentsConfig.get_solo().config_path
    if not config_path:
        raise ValueError("No config_path is specified in AppointmentsConfig")
    config_class = import_string(config_path)
    client = config_class.get_solo().get_client()
    return client


def book_appointment_for_submission(submission: Submission) -> None:
    appointment_data = submission.get_merged_appointment_data()
    expected_information = [
        "productID",
        "locationID",
        "appStartTime",
        "clientLastName",
        "clientDateOfBirth",
    ]

    missing_appointment_information = []
    not_filled_in_appointment_information = []
    for key in expected_information:
        if key not in appointment_data:
            missing_appointment_information.append(key)
        elif not appointment_data.get(key):
            # Key was in form but not filled in
            not_filled_in_appointment_information.append(key)

    if len(missing_appointment_information) == len(expected_information):
        # Submission was never intended to make an appointment so just return
        return
    elif missing_appointment_information or not_filled_in_appointment_information:
        # Incomplete information to make an appointment
        error_information = ""
        if missing_appointment_information:
            error_information += (
                f"Missing information in form: "
                f"{', '.join(missing_appointment_information)}. "
            )
        if not_filled_in_appointment_information:
            error_information += (
                f"Information not filled in by user: "
                f"{', '.join(not_filled_in_appointment_information)}. "
            )
        AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.missing_info,
            error_information=error_information,
            submission=submission,
        )
        return

    product = AppointmentProduct(identifier=str(appointment_data["productID"]), name="")
    location = AppointmentLocation(identifier=appointment_data["locationID"], name="")
    appointment_client = AppointmentClient(
        last_name=appointment_data["clientLastName"],
        birthdate=datetime.strptime(
            appointment_data["clientDateOfBirth"], "%Y-%m-%d"
        ).date(),
    )
    start_at = datetime.strptime(appointment_data["appStartTime"], "%Y-%m-%dT%H:%M:%S")

    try:
        client = get_client()
        appointment_id = client.create_appointment(
            [product], location, start_at, appointment_client
        )
        submission.appointment_information = f"Appointment Id: {appointment_id}"
        AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.success,
            appointment_id=appointment_id,
            submission=submission,
        )
    except AppointmentCreateFailed as e:
        AppointmentInfo.objects.create(
            status=AppointmentDetailsStatus.failed,
            error_information="Failed to make appointment",
            submission=submission,
        )


def create_base64_qrcode(text):
    img = qrcode.make(text)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("ascii")
