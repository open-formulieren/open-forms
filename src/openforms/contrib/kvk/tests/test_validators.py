from django.core.exceptions import ValidationError
from django.test import TestCase

from openforms.contrib.kvk.validators import validate_kvk


class KvKValidatorTestCase(TestCase):
    @staticmethod
    def test_valid_kvks():
        validate_kvk("12345678")

    def test_invalid_kvks(self):
        with self.assertRaises(ValidationError):
            validate_kvk("1234567890")

        with self.assertRaises(ValidationError):
            validate_kvk("1234567a")

        with self.assertRaises(ValidationError):
            validate_kvk("1234-567")
