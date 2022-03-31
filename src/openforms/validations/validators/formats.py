from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import phonenumbers
from phonenumbers import NumberParseException

from openforms.validations.registry import register


class PhoneNumberBaseValidator:
    country = None
    country_name = ""
    error_message = _("Not a valid %(country)s phone number")

    def __call__(self, value):
        try:
            z = phonenumbers.parse(value, self.country)
            if not phonenumbers.is_possible_number(
                z
            ) or not phonenumbers.is_valid_number(z):
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

        except NumberParseException:
            raise ValidationError(
                self.error_message,
                params={"country": self.country_name},
                code="invalid",
            )


@register("phonenumber-international", verbose_name=_("International phone number"))
class InternationalPhoneNumberValidator(PhoneNumberBaseValidator):
    country = None
    country_name = _("international")


@register("phonenumber-nl", verbose_name=_("Dutch phone number"))
class DutchPhoneNumberValidator(PhoneNumberBaseValidator):
    country = "NL"
    country_name = _("Dutch")
