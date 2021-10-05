import base64
import io
from datetime import datetime
from typing import List

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
            "No registration attempted because of incomplete information. ",
            should_retry=False,
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
    )
    start_at = datetime.strptime(
        appointment_data["appStartTime"]["value"], "%Y-%m-%dT%H:%M:%S%z"
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
