from django.test import TestCase

import requests_mock

from ..client import BAGClient
from .base import BagTestMixin


class BAGClientTests(BagTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_client_returns_street_name_and_city(self, m):
        m.get(
            "https://bag/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("bagapiprofileoas3.yaml"),
        )
        m.get(
            "https://bag/api/adressen?postcode=1015CJ&huisnummer=117",
            status_code=200,
            json=self.load_json_mock("addresses.json"),
        )

        address_data = BAGClient.get_address("1015CJ", 117)

        self.assertEqual(address_data["street_name"], "Keizersgracht")
        self.assertEqual(address_data["city"], "Amsterdam")

    @requests_mock.Mocker()
    def test_client_returns_empty_value_when_no_results_are_found(self, m):
        m.get(
            "https://bag/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("bagapiprofileoas3.yaml"),
        )
        m.get(
            "https://bag/api/adressen?postcode=1015CJ&huisnummer=1",
            status_code=200,
            json={},
        )

        address_data = BAGClient.get_address("1015CJ", 1)

        self.assertEqual(address_data, {})
