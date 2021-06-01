import datetime
import requests
from typing import NoReturn

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.submissions.models import Submission

from .client import QmaticOrchestraCalendarClient
from ...registry import register


class QmaticAppointmentOptionsSerializer(serializers.Serializer):
    orchestra_calendar_base_url = serializers.URLField(
        required=False,
        help_text=_(
            "Base URL of the Qmatic Orchestra Calendar service in which the "
            "appointments will be created."
        ),
    )
    branch_id_field_name = serializers.CharField(
        required=False,
        help_text=_(
            "The name of the form field that is used to determine the branch public ID "
            "in Qmatic Orchestra Calendar"
        )
    )
    service_id_field_name = serializers.CharField(
        required=False,
        help_text=_(
            "The name of the form field that is used to determine the service public ID "
            "in Qmatic Orchestra Calendar"
        )
    )


@register(
    "qmatic",
    _("Qmatic Orchestra Calendar"),
    configuration_options=QmaticAppointmentOptionsSerializer,
    # backend_feedback_serializer=BackendFeedbackSerializer,
)
def create_qmatic_appointment(submission: Submission, options: dict) -> NoReturn:
    import ipdb; ipdb.set_trace()
    qmatic_client = QmaticOrchestraCalendarClient(
        options["orchestra_calendar_base_url"]
    )

    submission_data = submission.get_merged_data()

    # TODO get field name from options, should probably be separate fields for
    # date and time
    submitted_datetime = datetime.datetime.fromisoformat(submission_data["datum"])
    date = submitted_datetime.date()
    time = submitted_datetime.time()

    branch_public_id = submission_data.get(options["branch_id_field_name"])
    service_public_id = submission_data.get(options["service_id_field_name"])

    response = qmatic_client.book_appointment(
        branch_public_id,
        service_public_id,
        date,
        time,
    )

    # TODO handle possible responses

    return response

