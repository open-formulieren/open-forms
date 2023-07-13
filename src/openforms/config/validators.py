import decimal

from django.core.validators import DecimalValidator
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _, ngettext_lazy


class FloatValidator(DecimalValidator):
    messages = {
        "invalid": _("Enter a valid float."),
        "max_digits": ngettext_lazy(
            "Ensure that there are no more than %(max)s digit in total.",
            "Ensure that there are no more than %(max)s digits in total.",
            "max",
        ),
        "max_decimal_places": ngettext_lazy(
            "Ensure that there are no more than %(max)s decimal place.",
            "Ensure that there are no more than %(max)s decimal places.",
            "max",
        ),
        "max_whole_digits": ngettext_lazy(
            "Ensure that there are no more than %(max)s digit before the decimal point.",
            "Ensure that there are no more than %(max)s digits before the decimal point.",
            "max",
        ),
    }

    def __call__(self, value):
        if not isinstance(value, float):
            raise ValidationError(
                self.messages["invalid"], code="invalid", params={"value": value}
            )

        float_to_string = str(value)
        string_to_decimal = decimal.Decimal(float_to_string)

        super(FloatValidator, self).__call__(string_to_decimal)
