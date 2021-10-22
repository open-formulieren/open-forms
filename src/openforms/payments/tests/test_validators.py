from django.core.exceptions import ValidationError
from django.test import TestCase

from openforms.payments.validators import validate_payment_order_id_prefix


class PaymentOrderIDValidatorTests(TestCase):
    def test_valid_prefixes(self):
        valid = [
            "",
            "ab",
            "12",
            "ab12",
            # placeholder
            "{year}" "aa{year}" "a1{year}a1",
        ]

        for value in valid:
            with self.subTest(value=value):
                validate_payment_order_id_prefix(value)

    def test_raises_for_invalid_prefixes(self):
        invalid = [
            " ",
            "aa ",
            " aa",
            "a-2",
            "{yearrr",
            "{bad}",
        ]

        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_payment_order_id_prefix(value)
