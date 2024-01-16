from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_verwerking_header(value: str) -> None:
    if value.count("@") > 1:
        raise ValidationError(
            _("The x-verwerking header must contain at most one '@' character."),
            code="no_multiple_at_characters",
        )
