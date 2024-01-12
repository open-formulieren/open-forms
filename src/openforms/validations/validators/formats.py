from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumber

from openforms.validations.base import BasePlugin
from openforms.validations.registry import register


class PhoneNumberBaseValidatorMixin:
    country: str | None
    country_name: str = ""
    error_message = _("Not a valid %(country)s phone number")

    def validate(self, value: str):
        z = self._parse_phonenumber(value)

        if not phonenumbers.is_possible_number(z) or not phonenumbers.is_valid_number(
            z
        ):
            raise ValidationError(
                self.error_message,
                params={"country": self.country_name},
                code="invalid",
            )

        # this additional check is needed because while .parse() does some checks on country
        #   is_possible_number() and is_valid_number() do not
        #   eg: country=NL would accept "+442083661177"
        if self.country:
            if not phonenumbers.is_valid_number_for_region(z, self.country):
                raise ValidationError(
                    self.error_message,
                    params={"country": self.country_name},
                    code="invalid",
                )


@register("phonenumber-international")
class InternationalPhoneNumberValidator(PhoneNumberBaseValidatorMixin, BasePlugin[str]):
    country = None
    country_name = _("international")
    error_message = _(
        "Not a valid international phone number. An example of a valid international phone number is +31612312312"
    )

    verbose_name = _("International phone number")
    for_components = ("phoneNumber",)

    def _parse_phonenumber(self, value: str) -> PhoneNumber:
        try:
            return phonenumbers.parse(value, self.country)
        except NumberParseException:
            # Issue #1828 - International phone numbers starting with "00" instead of "+" can't be parsed
            if value.startswith("00"):
                value = value.replace("00", "+", 1)
                return self._parse_phonenumber(value)

            raise ValidationError(
                self.error_message,
                code="invalid",
            )

    def __call__(self, value: str, submission):
        self.validate(value)


@register("phonenumber-nl")
class DutchPhoneNumberValidator(PhoneNumberBaseValidatorMixin, BasePlugin[str]):
    country = "NL"
    country_name = _("Dutch")
    error_message = _(
        "Not a valid dutch phone number. An example of a valid dutch phone number is 0612312312"
    )

    verbose_name = _("Dutch phone number")
    for_components = ("phoneNumber",)

    def _parse_phonenumber(self, value: str) -> PhoneNumber:
        try:
            return phonenumbers.parse(value, self.country)
        except NumberParseException:
            raise ValidationError(
                self.error_message,
                code="invalid",
            )

    def __call__(self, value: str, submission):
        self.validate(value)
