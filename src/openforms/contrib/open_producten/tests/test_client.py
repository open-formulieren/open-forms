from django.test import TestCase

import requests_mock
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.open_producten.client import (
    NoServiceConfigured,
    OpenProductenClient,
    get_open_producten_client,
)
from openforms.contrib.open_producten.models import OpenProductenConfig


class TestOpenProductenClient(TestCase):
    def setUp(self):
        self.client = OpenProductenClient(base_url="https://test")
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)

    def test_get_current_prices(self):

        self.requests_mock.get(
            json={
                "id": "f714ce89-0c98-4249-9e03-9fc929a29a09",
                "name": "test",
                "upl_name": "UPL-naam nog niet beschikbaar",
                "upl_uri": "http://standaarden.overheid.nl/owms/terms/UPL-naam_nog_niet_beschikbaar",
                "current_price": {
                    "id": "1ec25528-4c6b-4bbf-84f7-d0a3efdbe314",
                    "options": [
                        {
                            "id": "1c3cc677-b643-46f7-8f30-cbc18e297cad",
                            "amount": "24.00",
                            "description": "normaal",
                        }
                    ],
                    "valid_from": "2024-10-23",
                },
            },
            status_code=200,
            url="https://test/producttypes/current-prices",
        )

        product_type = self.client.get_current_prices()
        self.assertEqual(product_type.name, "test")
        self.assertEqual(product_type.id, "f714ce89-0c98-4249-9e03-9fc929a29a09")
        self.assertEqual(
            product_type.current_price.id, "1ec25528-4c6b-4bbf-84f7-d0a3efdbe314"
        )
        self.assertEqual(
            product_type.current_price.options[0].id,
            "1c3cc677-b643-46f7-8f30-cbc18e297cad",
        )
        self.assertEqual(product_type.current_price.options[0].amount, "24.00")

    def test_get_open_producten_client_without_service(self):
        OpenProductenConfig.objects.create()

        with self.assertRaisesMessage(
            NoServiceConfigured, "No open producten service configured!"
        ):
            get_open_producten_client()

    def test_get_open_producten_client_with_service(self):
        service = ServiceFactory(api_root="http://test")
        OpenProductenConfig.objects.create(producten_service=service)

        client = get_open_producten_client()
        self.assertEqual(client.base_url, "http://test/")
