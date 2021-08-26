from datetime import datetime

from openforms.appointments.base import (
    AppointmentClient,
    AppointmentLocation,
    AppointmentProduct,
)
from openforms.appointments.contrib.jcc.models import JccConfig
from openforms.appointments.exceptions import AppointmentCreateFailed
from openforms.submissions.models import Submission


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
        if missing_appointment_information:
            submission.appointment_information += f"Missing information in form: {', '.join(missing_appointment_information)}. "
        if not_filled_in_appointment_information:
            submission.appointment_information += f"Information not filled in by user: {', '.join(not_filled_in_appointment_information)}. "
        submission.save()
        return

    product = AppointmentProduct(identifier=str(appointment_data["productID"]), name="")
    location = AppointmentLocation(identifier=appointment_data["locationID"], name="")
    appointment_client = AppointmentClient(
        last_name=appointment_data["clientLastName"],
        birthdate=appointment_data["clientDateOfBirth"],
    )
    start_at = datetime.strptime("2021-08-25T17:00:00", "%Y-%m-%dT%H:%M:%S")

    try:
        config = JccConfig.get_solo()
        client = config.get_client()
        appointment_id = client.create_appointment(
            [product], location, start_at, appointment_client
        )
        submission.appointment_information = f"Appointment Id: {appointment_id}"
    except AppointmentCreateFailed as e:
        submission.appointment_information = "Failed to make appointment"
    finally:
        submission.save()
