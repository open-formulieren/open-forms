from typing import NoReturn

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.submissions.models import Submission

from ...registry import register


class DemoAppointmentOptionsSerializer(serializers.Serializer):
    locatie = serializers.CharField(
        required=False, help_text=_("Location of the appointment")
    )
    product = serializers.CharField(
        required=False,
        help_text=_("Product for which the appointment is made"),
    )


@register(
    "demo",
    _("Demo"),
    configuration_options=DemoAppointmentOptionsSerializer,
    # backend_feedback_serializer=BackendFeedbackSerializer,
)
def create_demo_appointment(submission: Submission, options: dict) -> NoReturn:
    print(f"Options for create_demo_appointment {options}")
