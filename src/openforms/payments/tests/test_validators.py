from django.core.exceptions import ValidationError
from django.test import TestCase

from openforms.payments.validators import validate_payment_order_id_prefix


class RegistryTests(TestCase):
    def test_validate_payment_order_id_prefix(self):
        validate_payment_order_id_prefix("")
        validate_payment_order_id_prefix("ab")
        validate_payment_order_id_prefix("12")
        validate_payment_order_id_prefix("ab12")

        validate_payment_order_id_prefix("{year}")
        validate_payment_order_id_prefix("aa{year}")
        validate_payment_order_id_prefix("a1{year}a1")

        with self.assertRaises(ValidationError):
            validate_payment_order_id_prefix(" ")

        with self.assertRaises(ValidationError):
            validate_payment_order_id_prefix("aa ")

        with self.assertRaises(ValidationError):
            validate_payment_order_id_prefix(" aa")

        with self.assertRaises(ValidationError):
            validate_payment_order_id_prefix("a-2")

        with self.assertRaises(ValidationError):
            validate_payment_order_id_prefix("{yearrr")

        with self.assertRaises(ValidationError):
            validate_payment_order_id_prefix("{bad}")
