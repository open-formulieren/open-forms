from decimal import Decimal
from uuid import uuid4

from django.db import IntegrityError
from django.test import TestCase

from openforms.products.tests.factories import ProductFactory


class ProductTestCase(TestCase):
    def test_price_without_producttype(self):
        ProductFactory.create(price=Decimal(350.0), producttype=None)

    def test_producttype_without_price(self):
        ProductFactory.create(price=None, producttype=uuid4())

    def test_price_with_producttype(self):
        with self.assertRaises(IntegrityError):
            ProductFactory.create(price=Decimal(350.0), producttype=uuid4())

    def test_without_price_and_producttype(self):
        with self.assertRaises(IntegrityError):
            ProductFactory.create(price=None, producttype=None)
