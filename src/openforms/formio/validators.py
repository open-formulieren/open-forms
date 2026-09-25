from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

# Regex and message adapted from
# https://github.com/formio/formio.js/blob/4.13.x/src/components/_classes/component/editForm/Component.edit.api.js#L10
variable_key_validator = RegexValidator(
    regex=_lazy_re_compile(r"^(\w|\w[\w.\-]*\w)$"),
    message=_(
        "Invalid variable key. "
        "It must only contain alphanumeric characters, underscores, "
        "dots and dashes and should not be ended by dash or dot."
    ),
)


def validate_formio_js_schema(value: dict):
    """
    Validate that the passed in value conforms to FormIO.js JSON schema.

    So far, we haven't been able to find a formal description of the schema, so we're
    sticking to what the form builder outputs.
    """
    # very bare-bones checks
    if not isinstance(value, dict):
        raise ValidationError(
            _("Top-level value must be an Object."),
            code="invalid",
        )

    components = value.get("components")
    if components is None:
        raise ValidationError(
            _("Top-level key 'components' is missing."),
            code="invalid",
        )

    if not isinstance(components, list):
        raise ValidationError(
            _("The 'components' value must be a list of components."),
            code="invalid",
        )


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
