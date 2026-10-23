from django.test import TestCase

from ..client import get_open_product_client
from ..constants import OpenProductApiOptions
from ..exceptions import NoServiceConfigured
from ..models import ProductConfiguration
from .factories import OpenProductServiceFactory


class ProductConfigurationAdminTests(TestCase):
    def test_client_not_configured(self):
        with self.assertRaises(NoServiceConfigured):
            get_open_product_client(OpenProductApiOptions.product_type, None)

    def test_changing_from_product_to_producttype_api_updates_service(self):
        op_service = OpenProductServiceFactory.create(
            api_root="http://localhost:8006/producten/api/v1/"
        )
        config = ProductConfiguration.get_solo()
        config.open_product_service = op_service
        config.save()

        get_open_product_client(OpenProductApiOptions.product_type, op_service)

        self.assertEqual(
            config.open_product_service.api_root,
            "http://localhost:8006/producttypen/api/v1/",
        )
