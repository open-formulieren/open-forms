from decimal import Decimal
from uuid import uuid4

from django.db import IntegrityError
from django.test import TestCase

from ..constants import ProductSourceChoices
from .factories import ProductFactory


class ProductTestCase(TestCase):
    def test_local_product_price_without_producttype_should_pass(self):
        try:
            ProductFactory.create(price=Decimal(350.0), producttype_uuid=None)
        except IntegrityError as exc:
            raise self.failureException(
                "Local products should be able to set a price."
            ) from exc

    def test_external_product_with_producttype_and_without_price_should_pass(self):
        try:
            ProductFactory.create(
                product_source=ProductSourceChoices.open_product,
                price=None,
                producttype_uuid=uuid4(),
            )
        except IntegrityError as exc:
            raise self.failureException(
                "External product prices should be empty."
            ) from exc

    def test_local_product_with_price_producttype_should_fail(self):
        with self.assertRaises(IntegrityError):
            ProductFactory.create(
                product_source=ProductSourceChoices.local,
                price=Decimal(350.0),
                producttype_uuid=uuid4(),
            )

    def test_local_product_without_price_and_producttype_should_fail(self):
        with self.assertRaises(IntegrityError):
            ProductFactory.create(
                product_source=ProductSourceChoices.local,
                price=None,
                producttype_uuid=None,
            )
