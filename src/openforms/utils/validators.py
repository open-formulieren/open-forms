from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _

validate_digits = RegexValidator(
    regex="^[0-9]+$", message=_("Expected a numerical value.")
)


class Proef11ValidatorBase:
    value_size = NotImplemented
    error_messages = {
        "too_short": NotImplemented,
        "wrong": NotImplemented,
    }

    def __call__(self, value):
        """
        Validates that a string value is a valid 11-proef number (BSN, RSIN etc) by applying the
        '11-proef' checking.
        :param value: String object representing a presumably good 11-proef number.
        """
        # Initial sanity checks.
        validate_digits(value)
        if len(value) != self.value_size:
            raise ValidationError(
                self.error_messages["too_short"],
                params={"size": self.value_size},
                code="invalid",
            )

        # 11-proef check.
        total = 0
        for multiplier, char in enumerate(reversed(value), start=1):
            if multiplier == 1:
                total += -multiplier * int(char)
            else:
                total += multiplier * int(char)

        if total % 11 != 0:
            raise ValidationError(self.error_messages["wrong"])


@deconstructible
class BSNValidator(Proef11ValidatorBase):
    value_size = 9
    error_messages = {
        "too_short": _("BSN should have %(size)i characters."),
        "wrong": _("Invalid BSN."),
    }


@deconstructible
class RSINValidator(Proef11ValidatorBase):
    value_size = 9
    error_messages = {
        "too_short": _("RSIN should have %(size)i characters."),
        "wrong": _("Invalid RSIN."),
    }


validate_bsn = BSNValidator()
validate_rsin = RSINValidator()


@deconstructible
class KVKValidator:
    value_size = 8
    error_messages = {
        "too_short": _("KvK number should have %(size)i characters."),
    }

    def __call__(self, value):
        validate_digits(value)

        if len(value) != self.value_size:
            raise ValidationError(
                self.error_messages["too_short"],
                params={"size": self.value_size},
                code="invalid",
            )


validate_kvk = KVKValidator()
