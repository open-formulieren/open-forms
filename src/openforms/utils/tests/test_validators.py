from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ..validators import validate_bsn, validate_iban, validate_rsin


class BSNValidatorTestCase(SimpleTestCase):
    @staticmethod
    def test_valid_bsns():
        validate_bsn("063308836")
        validate_bsn("619183020")

    def test_invalid_bsns(self):
        with self.assertRaises(ValidationError):
            validate_bsn("06330883")

        with self.assertRaises(ValidationError):
            validate_bsn("063a08836")

        with self.assertRaises(ValidationError):
            validate_bsn("063-08836")


class RSINValidatorTestCase(SimpleTestCase):
    @staticmethod
    def test_valid_bsns():
        validate_rsin("063308836")
        validate_rsin("619183020")

    def test_invalid_bsns(self):
        with self.assertRaises(ValidationError):
            validate_rsin("06330883")

        with self.assertRaises(ValidationError):
            validate_rsin("063a08836")

        with self.assertRaises(ValidationError):
            validate_rsin("063-08836")


class IBANValidatorTestCase(SimpleTestCase):
    def test_valid_ibans(self):
        validate_iban("NL02ABNA0123456789")
        validate_iban("NL14 ABNA 1238 8878 00")

    def test_invalid_ibans(self):
        with self.assertRaises(ValidationError):
            validate_iban("NL12 3456 789I I987 6999")

        with self.assertRaises(ValidationError):
            validate_iban("DX89 3704 0044 0532 0130 00")

        with self.assertRaises(ValidationError):
            validate_iban("DE20 2909 0900 8840 0170 9000")

        with self.assertRaises(ValidationError):
            validate_iban("DEo20 2909 0900 8840 0170 00")
