from dataclasses import dataclass

from django.utils.translation import gettext as _

from rest_framework import serializers


@dataclass
class PrivacyPolicyInfo:
    requires_privacy_consent: bool
    privacy_label: str


class PrivacyPolicyInfoSerializer(serializers.Serializer):
    requires_privacy_consent = serializers.BooleanField(
        help_text=_(
            "Whether the user must agree to the privacy policy before submitting a form."
        )
    )
    privacy_label = serializers.CharField(
        help_text=_(
            "The formatted label to use next to the checkbox when asking the user to agree to the privacy policy."
        )
    )
