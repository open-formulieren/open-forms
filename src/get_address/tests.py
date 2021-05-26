from unittest.mock import patch

from django.template import loader
from django.test import TestCase

from get_address.get_address import get_person_address


class GetAddressTest(TestCase):
    @patch("get_address.stuf_bg.models.StufBGConfig.get_solo")
    def test_get_address(self, client_mock):
        client_mock.return_value.get_client.return_value.get_address.return_value = loader.render_to_string(
            "get_address/stuf_bg/tests/responses/ResponseAddress.xml"
        )

        address = get_person_address("123456789")

        self.assertEqual(address["street_name"], "Keizersgracht")
        self.assertEqual(address["house_number"], "117")
        self.assertEqual(address["house_letter"], "A")
        self.assertEqual(address["house_letter_addition"], "B")
        self.assertEqual(address["postcode"], "1015 CJ")
        self.assertEqual(address["city"], "Amsterdam")
