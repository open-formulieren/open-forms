from django.test import TestCase

from openforms.authentication.constants import AuthAttribute
from openforms.utils.tests.vcr import OFVCRMixin

from ..client import get_customer_interactions_client
from .mixins import CustomerInteractionsMixin
from .typing import ExpectedDigitalAddress


class CustomerInteractionsClientTest(CustomerInteractionsMixin, OFVCRMixin, TestCase):
    def test_list_digital_addresses_for_bsn(self):
        with get_customer_interactions_client(self.config) as client:
            data = list(
                client.get_digital_addresses(
                    auth_attribute=AuthAttribute.bsn, auth_value="123456782"
                )
            )

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

    def test_list_digital_addresses_empty_for_bsn(self):
        with get_customer_interactions_client(self.config) as client:
            data = list(
                client.get_digital_addresses(
                    auth_attribute=AuthAttribute.bsn, auth_value="123456780"
                )
            )

        self.assertEqual(len(data), 0)

    def test_list_digital_addresses_for_kvk(self):
        with get_customer_interactions_client(self.config) as client:
            data = list(
                client.get_digital_addresses(
                    auth_attribute=AuthAttribute.kvk, auth_value="12345678"
                )
            )

        expected_addresses: list[ExpectedDigitalAddress] = [
            {
                "adres": "0612345678",
                "soortDigitaalAdres": "telefoonnummer",
                "isStandaardAdres": True,
            },
            {
                "adres": "maykinmail@test.com",
                "soortDigitaalAdres": "email",
                "isStandaardAdres": True,
            },
        ]
        self.assertEqual(len(data), 2)
        for expected_address in expected_addresses:
            with self.subTest(expected_address["adres"]):
                self.assertAddressPresent(data, expected_address)

    def test_list_digital_addresses_empty_for_kvk(self):
        with get_customer_interactions_client(self.config) as client:
            data = list(
                client.get_digital_addresses(
                    auth_attribute=AuthAttribute.kvk, auth_value="11122233"
                )
            )

        self.assertEqual(len(data), 0)

    def test_list_digital_addresses_for_unsupported_auth_attribute(self):
        with get_customer_interactions_client(self.config) as client:
            with self.assertRaisesMessage(
                NotImplementedError,
                "Only bsn and kvk authentications are supported for Customer Interactions API",
            ):
                client.get_digital_addresses(
                    auth_attribute=AuthAttribute.pseudo, auth_value="11122233"
                )
