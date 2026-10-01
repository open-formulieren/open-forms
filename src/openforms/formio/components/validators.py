from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class EmailVerificationValidator:
    message = _("The email address {value} has not been verified yet.")
    requires_context = True

    component_key: str

    def __init__(self, component_key: str) -> None:
        self.component_key = component_key

    def __call__(self, value: str, field: serializers.Field) -> None:
        from openforms.submissions.models import EmailVerification, Submission

        assert isinstance(value, str)
        error_format = self.message.format(value=value)
        submission: Submission = field.context["submission"]
        has_verification = EmailVerification.objects.filter(
            submission=submission,
            component_key=self.component_key,
            email=value,
            verified_on__isnull=False,
        ).exists()

        if not has_verification:
            raise serializers.ValidationError(error_format, code="unverified")
