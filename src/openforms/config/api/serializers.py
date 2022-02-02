from dataclasses import dataclass

from django.utils.translation import gettext as _

from rest_framework import serializers

from csp_post_processor.drf.fields import CSPPostProcessedHTMLField


@dataclass
class PrivacyPolicyInfo:
    requires_privacy_consent: bool
    privacy_label: str = None


class PrivacyPolicyInfoSerializer(serializers.Serializer):
    requires_privacy_consent = serializers.BooleanField(
        help_text=_(
            "Whether the user must agree to the privacy policy before submitting a form."
        )
    )
    privacy_label = CSPPostProcessedHTMLField(
        help_text=_(
            "The formatted label to use next to the checkbox when asking the user to agree to the privacy policy."
        ),
        required=False,
    )
