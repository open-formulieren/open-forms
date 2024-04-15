from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from openforms.payments.validators import validate_payment_order_id_template


class PaymentOrderIDValidatorTests(SimpleTestCase):
    def test_uid_present(self):
        valid = "{uid}"
        with self.subTest(value=valid):
            validate_payment_order_id_template(valid)

        invalid = "other_things"
        with self.subTest(value=invalid):
            with self.assertRaises(ValidationError):
                validate_payment_order_id_template(invalid)

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
                validate_payment_order_id_template(value)

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
                    validate_payment_order_id_template(value)
