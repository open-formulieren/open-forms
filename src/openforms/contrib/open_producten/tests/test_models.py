import datetime
from decimal import Decimal
from uuid import UUID

from django.test import TestCase

from freezegun import freeze_time

from openforms.contrib.open_producten.tests.factories import (
    PriceFactory,
    PriceOptionFactory,
)
from openforms.products.tests.factories import ProductFactory


@freeze_time("2024-02-01")
class TestProductType(TestCase):

    def setUp(self):
        self.product = ProductFactory()

    def test_open_producten_price_with_valid_price(self):
        price = PriceFactory(
            valid_from=datetime.date(2024, 1, 1), product_type=self.product
        )

        self.assertEqual(self.product.open_producten_price.uuid, UUID(price.uuid))

    def test_open_producten_price_with_no_invalid_prices(self):
        PriceFactory(valid_from=datetime.date(2024, 3, 1), product_type=self.product)

        self.assertEqual(self.product.prices.count(), 1)
        self.assertEqual(self.product.open_producten_price, None)

    def test_open_producten_price_with_no_prices(self):
        self.assertEqual(self.product.open_producten_price, None)


class TestPrice(TestCase):

    def test_str(self):
        price = PriceFactory(
            product_type__upl_name="test", valid_from=datetime.date(2024, 1, 1)
        )
        self.assertEqual(str(price), "test 2024-01-01")


class TestPriceOption(TestCase):

    def test_str(self):
        price = PriceOptionFactory(description="test", amount=Decimal("19.23"))
        self.assertEqual(str(price), "test 19.23")
