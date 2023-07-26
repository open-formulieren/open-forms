from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from soap.tests.factories import SoapServiceFactory

from ..validators import validate_bsn, validate_rsin, validate_service_url_not_empty


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


class ServiceURLEmptyTestCase(TestCase):
    def test_valid_service(self):
        service = SoapServiceFactory()
        result = validate_service_url_not_empty(service.pk)

        self.assertIsNone(result)

    def test_invalid_service(self):
        service = SoapServiceFactory(url="")

        with self.assertRaises(ValidationError):
            validate_service_url_not_empty(service.pk)
