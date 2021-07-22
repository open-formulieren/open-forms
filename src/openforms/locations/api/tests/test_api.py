from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class GetStreetNameAndCityViewAPITests(TestCase):
    @patch("openforms.locations.api.views.import_string")
    def test_getting_street_name_and_city(self, import_string_mock):
        import_string_mock.return_value.get_address.return_value = {
            "street_name": "Keizersgracht",
            "city": "Amsterdam",
        }

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ&house_number=117"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()["streetName"], "Keizersgracht")
        self.assertEqual(response.json()["city"], "Amsterdam")

    def test_getting_street_name_and_city_without_post_code(self):

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?house_number=117"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"postcode": ["Dit veld is vereist."]})

    def test_getting_street_name_and_city_without_house_number(self):

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"houseNumber": ["Dit veld is vereist."]})

    @patch("openforms.locations.api.views.import_string")
    def test_getting_street_name_and_city_with_extra_query_params(
        self, import_string_mock
    ):
        import_string_mock.return_value.get_address.return_value = {
            "street_name": "Keizersgracht",
            "city": "Amsterdam",
        }

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ&house_number=117&random=param"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()["streetName"], "Keizersgracht")
        self.assertEqual(response.json()["city"], "Amsterdam")

    @patch("openforms.locations.api.views.import_string")
    def test_address_not_found(self, import_string_mock):
        import_string_mock.return_value.get_address.return_value = {}

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ&house_number=1"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
        self.assertEqual(response.json(), {})
