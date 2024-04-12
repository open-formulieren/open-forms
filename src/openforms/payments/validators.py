from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_payment_order_id_template(value: str) -> None:
    if "{uid}" not in value:
        raise ValidationError(_("The template should include the {uid} placeholder."))

    for allowed in ["{year}", "{reference}", "{uid}", "/", ".", "_", "-"]:
        value = value.replace(allowed, "")

    if value and not value.isalnum():
        raise ValidationError(_("The template should be alphanumeric."))
