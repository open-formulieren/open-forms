from typing import TypedDict

from django.test import TestCase

from openklant_client.types.resources.digitaal_adres import SoortDigitaalAdres

from openforms.utils.tests.vcr import OFVCRMixin

from ..client import get_customer_interactions_client
from .factories import CustomerInteractionsAPIGroupConfigFactory


class ExpectedDigitalAddress(TypedDict):
    """Partial of openklant_client.DigitaalAdres with only necessary properties."""

    adres: str
    soortDigitaalAdres: SoortDigitaalAdres
    isStandaardAdres: bool


class CustomerInteractionsClientTest(OFVCRMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.config = CustomerInteractionsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def assertAddressPresent(self, results, expected_address: ExpectedDigitalAddress):
        adres = expected_address["adres"]
        found_address = next((da for da in results if da["adres"] == adres), None)
        for property, expected_value in expected_address.items():
            self.assertEqual(
                expected_value, found_address[property], f"for address {adres}"
            )

    def test_list_digital_addresses(self):
        with get_customer_interactions_client(self.config) as client:
            data = list(client.get_digital_addresses_for_bsn(bsn="123456782"))

        expected_addresses: list[ExpectedDigitalAddress] = [
            {
                "adres": "0687654321",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": False,
            },
            {
                "adres": "0612345678",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": True,
            },
            {
                "adres": "someemail@example.org",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": False,
            },
            {
                "adres": "devilkiller@example.org",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": False,
            },
            {
                "adres": "john.smith@gmail.com",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": True,
            },
        ]
        self.assertEqual(len(data), 5)
        for expected_address in expected_addresses:
            with self.subTest(expected_address["adres"]):
                self.assertAddressPresent(data, expected_address)

    def test_list_digital_addresses_empty(self):
        with get_customer_interactions_client(self.config) as client:
            data = list(client.get_digital_addresses_for_bsn(bsn="123456780"))

        self.assertEqual(len(data), 0)
