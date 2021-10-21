from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_payment_order_id_prefix(value: str):
    value = value.replace("{year}", "")
    if value and not value.isalnum():
        raise ValidationError(
            _(
                "Prefix must be alpha numeric, no spaces or special characters except {year}"
            )
        )
