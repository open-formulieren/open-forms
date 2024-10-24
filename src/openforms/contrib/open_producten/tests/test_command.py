from io import StringIO
from unittest.mock import patch
from uuid import uuid4

from django.core.management import call_command
from django.test import TestCase

from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.open_producten.models import OpenProductenConfig
from openforms.contrib.open_producten.tests.factories import (
    PriceFactory,
    PriceOptionFactory,
)
from openforms.products.tests.factories import ProductFactory


class TestImportPrices(TestCase):

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "import_prices",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_import_prices_without_config(self):
        out = self.call_command()
        self.assertEqual(
            out, "Please define the OpenProductenConfig before running this command.\n"
        )

    @patch(
        "openforms.contrib.open_producten.management.commands.import_prices.get_open_producten_client"
    )
    @patch(
        "openforms.contrib.open_producten.management.commands.import_prices.PriceImporter.import_product_types"
    )
    def test_import_prices(self, mock_import_product_types, mock_client):
        OpenProductenConfig.objects.create(producten_service=ServiceFactory.create())

        uuid = uuid4()

        mock_import_product_types.return_value = (
            [
                ProductFactory.create(uuid=uuid),
                PriceFactory.create(uuid=uuid),
                PriceOptionFactory.create(uuid=uuid),
            ],
            [],
        )
        out = self.call_command()

        self.assertEqual(
            out,
            f"updated 0 exising product type(s)\ncreated 3 new product type(s):\nProduct: {uuid}\nPrice: {uuid}\nPriceOption: {uuid}\n",
        )
