from django.test import TestCase
from django.urls import reverse

import requests_mock
from zgw_consumers.test import mock_service_oas_get

from openforms.contrib.bag.api.tests.base import BagTestMixin


class GetStreetNameAndCityViewAPITests(BagTestMixin, TestCase):
    @requests_mock.Mocker()
    def test_getting_street_name_and_city(self, m):
        mock_service_oas_get(m, "https://bag/", service="bagapiprofileoas3")
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

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ&huisnummer=117"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()["streetName"], "Keizersgracht")
        self.assertEqual(response.json()["city"], "Amsterdam")

    def test_getting_street_name_and_city_without_post_code(self):

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?huisnummer=117"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'postcode': ['Dit veld is vereist.']})

    def test_getting_street_name_and_city_without_house_number(self):

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'huisnummer': ['Dit veld is vereist.']})

    @requests_mock.Mocker()
    def test_getting_street_name_and_city_with_extra_query_params(self, m):
        mock_service_oas_get(m, "https://bag/", service="bagapiprofileoas3")
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

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ&huisnummer=117&random=param"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()["streetName"], "Keizersgracht")
        self.assertEqual(response.json()["city"], "Amsterdam")
