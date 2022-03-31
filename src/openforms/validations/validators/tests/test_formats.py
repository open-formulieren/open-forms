from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext as _

from openforms.validations.validators.formats import (
    DutchPhoneNumberValidator,
    InternationalPhoneNumberValidator,
)


class ValidatorTestBase(TestCase):
    def run_cases(self, validator, valid, invalid, message):
        for value in valid:
            with self.subTest(f"valid '{value}'"):
                validator(value)

        for value in invalid:
            with self.subTest(f"invalid '{value}'"):
                with self.assertRaisesMessage(ValidationError, message):
                    validator(value)


class PhoneNumberTestCase(ValidatorTestBase):
    def test_phone_number_international(self):
        validator = InternationalPhoneNumberValidator()
        valid = [
            "+31612345678",
            "+441134960000",  # US test number
            "+1 206 555 0100",  # US test number
        ]
        invalid = [
            "",
            "xxxx",
            "06123456789",
            "020 753 0523",
            "+311234",
            "+3161234566789aaaaa",
        ]
        message = _("Not a valid %(country)s phone number") % {
            "country": _("international")
        }
        self.run_cases(validator, valid, invalid, message)

    def test_phone_number_dutch(self):
        validator = DutchPhoneNumberValidator()
        valid = [
            "+31612345678",
            "+31 612 345 678",
            "0612345678",
            "020 753 0523",
            "0207530523",
        ]
        invalid = [
            "",
            "xxxx",
            "061234567890",
            "+311234",
            "+3161234567890",
            "+3161234566789aaaaa",
            "+441134960000",  # US test number
            "+1 206 555 0100",  # US test number
        ]
        message = _("Not a valid %(country)s phone number") % {"country": _("Dutch")}
        self.run_cases(validator, valid, invalid, message)
