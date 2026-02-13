from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from openforms.payments.validators import IdTemplateValidator


class PaymentOrderIDValidatorTests(SimpleTestCase):
    def test_uid_present(self):
        valid = "{uid}"
        with self.subTest(value=valid):
            IdTemplateValidator()(valid)

        invalid = "other_things"
        with self.subTest(value=invalid):
            with self.assertRaises(ValidationError):
                IdTemplateValidator()(invalid)

    def test_valid_templates(self):
        valid = [
            "{uid}",
            "{uid}ab",
            "{uid}12",
            "{uid}ab12",
            "{uid}a-.///---_",
            # placeholders:
            "{uid}{year}",
            "{year}{public_reference}{uid}",
        ]

        for value in valid:
            with self.subTest(value=value):
                IdTemplateValidator()(value)

    def test_raises_for_invalid_prefixes(self):
        invalid = [
            " {uid}",
            "aa {uid}",
            " aa{uid}",
            "{yearrr{uid}",
            "{bad}{uid}",
        ]

        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    IdTemplateValidator()(value)
