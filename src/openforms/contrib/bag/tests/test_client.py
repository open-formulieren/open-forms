from django.test import TestCase

import requests_mock
from zds_client import ClientError
from zgw_consumers.test import mock_service_oas_get

from ..client import BAGClient
from .base import BagTestMixin


class BAGClientTests(BagTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_client_returns_street_name_and_city(self, m):
        mock_service_oas_get(m, "https://bag/api/", service="bagapiprofileoas3")
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
        mock_service_oas_get(m, "https://bag/api/", service="bagapiprofileoas3")
        m.get(
            "https://bag/api/adressen?postcode=1015CJ&huisnummer=1",
            status_code=200,
            json={},
        )

        address_data = BAGClient.get_address("1015CJ", 1)

        self.assertEqual(address_data, {})

    @requests_mock.Mocker()
    def test_client_returns_empty_value_when_client_exception_is_thrown(self, m):
        mock_service_oas_get(m, "https://bag/api/", service="bagapiprofileoas3")
        m.get(
            "https://bag/api/adressen?postcode=1015CJ&huisnummer=115", exc=ClientError
        )

        address_data = BAGClient.get_address("1015CJ", 115)

        self.assertEqual(address_data, {})
