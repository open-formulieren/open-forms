from collections.abc import Sequence

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from schwifty import IBAN

from openforms.utils.redirect import allow_redirect_url

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
    """
    Validate a BSN value by applying the "11-proef".
    """

    value_size = 9
    error_messages = {
        "too_short": _("BSN should have %(size)i characters."),
        "wrong": _("Invalid BSN."),
    }


@deconstructible
class RSINValidator(Proef11ValidatorBase):
    """
    Validate a RSIN value by applying the "11-proef".
    """

    value_size = 9
    error_messages = {
        "too_short": _("RSIN should have %(size)i characters."),
        "wrong": _("Invalid RSIN."),
    }


validate_bsn = BSNValidator()
validate_rsin = RSINValidator()


@deconstructible
class UniqueValuesValidator:
    """
    Validate a collection of unique values.
    """

    message = _("Values must be unique")
    code = "invalid"

    def __call__(self, value: list[str]):
        uniq = set(value)
        if len(uniq) != len(value):
            raise ValidationError(self.message, code=self.code)


@deconstructible
class AllowedRedirectValidator:
    """
    Validate that a redirect target is not an open redirect.
    """

    message = _("URL is not on the domain whitelist")
    code = "invalid"

    def __call__(self, value: str):
        if not allow_redirect_url(value):
            raise ValidationError(self.message, code=self.code)


@deconstructible
class SerializerValidator:
    """
    Validate a value against a DRF serializer class.
    """

    message = _("The data shape does not match the expected shape: {errors}")
    code = "invalid"

    def __init__(self, serializer_cls: type[serializers.Serializer], many=False):
        self.serializer_cls = serializer_cls
        self.many = many

    def __call__(self, value):
        if not value:
            return

        serializer = self.serializer_cls(data=value, many=self.many)
        if not serializer.is_valid():
            raise ValidationError(
                self.message.format(errors=serializer.errors),
                code=self.code,
            )


@deconstructible
class IBANValidator:
    message = _("Invalid IBAN")
    code = "invalid"

    def __call__(self, value):
        iban = IBAN(value, allow_invalid=True)

        if not iban.is_valid:
            raise ValidationError(self.message, code=self.code)


validate_iban = IBANValidator()


@deconstructible
class IdTemplateValidator:
    def __init__(
        self,
        allowed_groups: Sequence[str] = (
            "{year}",
            "{public_reference}",
            "{uid}",
            "/",
            ".",
            "_",
            "-",
        ),
    ):
        self.allowed_groups = allowed_groups

    def __call__(self, value: str) -> None:
        if "{uid}" not in value:
            raise ValidationError(_("The template must include the {uid} placeholder."))

        for allowed in self.allowed_groups:
            value = value.replace(allowed, "")

        if value and not value.isalnum():
            # build human readable error message
            special_chars = [char for char in self.allowed_groups if len(char) == 1]
            if not special_chars:
                csv_chars = last_char = ""
                msg = _("The template may only consist of alphanumeric characters.")
            else:
                msg = _(
                    "The template may only consist of alphanumeric{csv_chars} and "
                    "{last_char} characters."
                )
                csv_chars = (
                    f", {', '.join(special_chars[:-1])}"
                    if len(special_chars) > 1
                    else ""
                )
                last_char = special_chars[-1]
            raise ValidationError(msg.format(csv_chars=csv_chars, last_char=last_char))
