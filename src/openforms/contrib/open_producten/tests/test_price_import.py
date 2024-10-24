from unittest.mock import MagicMock
from uuid import uuid4

from django.db import IntegrityError
from django.test import TestCase

from openforms.products.models import Product
from openforms.products.tests.factories import ProductFactory

from ..models import Price, PriceOption
from ..price_import import PriceImporter
from .factories import PriceFactory
from .helpers import create_price, create_price_option, create_product_type


class TestPriceImport(TestCase):

    def setUp(self):
        self.client = MagicMock()

    def test_handle_options(self):
        option_uuid = uuid4()
        price = PriceFactory()
        importer = PriceImporter(self.client)
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):
                option = create_price_option(option_uuid)
                importer._handle_options([option], price)
                instance = PriceOption.objects.first()

                self.assertEqual(Price.objects.count(), 1)
                self.assertEqual(instance.uuid, option_uuid)

    def test_update_or_create_price(self):
        price_uuid = uuid4()
        product = ProductFactory()
        importer = PriceImporter(self.client)
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):

                price = create_price(price_uuid, uuid4())
                importer._update_or_create_price(price, product)
                instance = Price.objects.first()

                self.assertEqual(Price.objects.count(), 1)
                self.assertEqual(instance.uuid, price_uuid)

    def test_create_price_unique_valid_from(self):
        product = ProductFactory()
        importer = PriceImporter(self.client)

        price = create_price(uuid4(), uuid4())
        importer._update_or_create_price(price, product)

        with self.assertRaises(IntegrityError):
            price = create_price(uuid4(), uuid4())
            importer._update_or_create_price(price, product)

    def test_handle_product_types(self):
        product_type_uuid = uuid4()
        price_uuid = uuid4()

        importer = PriceImporter(self.client)
        for create in (True, False):
            with self.subTest(
                "should create instance if uuid does not exist"
                if create
                else "should update instance if uuid exists"
            ):
                product_type = create_product_type(
                    product_type_uuid, price_uuid, uuid4()
                )
                importer._handle_product_types([product_type])
                instance = Product.objects.first()

                self.assertEqual(Product.objects.count(), 1)
                self.assertEqual(instance.uuid, product_type_uuid)

    def test_import_product_types(self):
        product_type = create_product_type(uuid4(), uuid4(), uuid4())
        self.client.get_current_prices.return_value = [product_type]

        importer = PriceImporter(self.client)
        created, updated = importer.import_product_types()

        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Price.objects.count(), 1)
        self.assertEqual(PriceOption.objects.count(), 1)

        product = Product.objects.first()
        price = Price.objects.first()
        option = PriceOption.objects.first()

        self.assertEqual(price.options.count(), 1)
        self.assertEqual(product.prices.count(), 1)

        self.assertEqual(product.open_producten_price, price)

        self.assertEqual(updated, [])
        self.assertEqual(created, [product, price, option])
