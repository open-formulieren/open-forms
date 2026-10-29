from decimal import Decimal
from uuid import uuid4

from django.db import IntegrityError
from django.test import TestCase

from openforms.products.tests.factories import ProductFactory


class ProductTestCase(TestCase):
    def test_price_without_producttype(self):
        try:
            ProductFactory.create(price=Decimal(350.0), producttype_uuid=None)
        except IntegrityError as exc:
            raise self.failureException(
                "Local products should be able to set a price."
            ) from exc

    def test_producttype_without_price(self):
        try:
            ProductFactory.create(price=None, producttype_uuid=uuid4())
        except IntegrityError as exc:
            raise self.failureException(
                "Open product products prices should be empty."
            ) from exc

    def test_price_with_producttype(self):
        with self.assertRaises(IntegrityError):
            ProductFactory.create(price=Decimal(350.0), producttype_uuid=uuid4())

    def test_without_price_and_producttype(self):
        with self.assertRaises(IntegrityError):
            ProductFactory.create(price=None, producttype_uuid=None)

    def test_uuid_follows_producttype(self):
        producttype_uuid = uuid4()
        product = ProductFactory.create(price=None, producttype_uuid=producttype_uuid)

        self.assertEqual(product.uuid, producttype_uuid)
