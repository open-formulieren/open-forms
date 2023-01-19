from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_no_trailing_slash(url: str) -> None:
    if url.endswith("/"):
        raise ValidationError(
            _("The URL must not end with a trailing slash ('/')."),
            code="no_trailing_slash",
        )
