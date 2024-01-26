"""
Tests for retrieving available appointment dates from Qmatic through our own API.
"""

from datetime import date

from django.test import TestCase

from openforms.utils.tests.vcr import OFVCRMixin

from ..plugin import QmaticAppointment
from .utils import TEST_FILES, MockConfigMixin

QMATIC_BASE_URL = "http://localhost:8080/qmatic/calendar-backend/public/api/"

plugin = QmaticAppointment("qmatic")


class ListAvailableDatesTests(OFVCRMixin, MockConfigMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # update the dummy service to point to the real service API root
        cls.service.api_root = QMATIC_BASE_URL
        cls.service.save()

    def setUp(self):
        super().setUp()

        locations = plugin.get_locations()
        self.location = next(
            location for location in locations if location.name == "KCC"
        )

    def test_listing_dates_single_product_single_customer(self):
        product = plugin.get_available_products(location_id=self.location.identifier)[0]
        assert product.amount == 1

        dates = plugin.get_dates(products=[product], location=self.location)

        self.assertGreater(len(dates), 0)
        self.assertIsInstance(dates[0], date)

    def test_listing_dates_single_product_multiple_customers(self):
        product = plugin.get_available_products(location_id=self.location.identifier)[0]
        product.amount = 999  # amount that should not return any dates

        with self.subTest("product.amount set"):
            dates = plugin.get_dates(products=[product], location=self.location)

            self.assertEqual(len(dates), 0)

        with self.subTest("product repeated"):
            product.amount = 1
            dates = plugin.get_dates(products=[product] * 999, location=self.location)

            self.assertEqual(len(dates), 0)

    def test_multiple_products_multiple_customers(self):
        products = plugin.get_available_products(location_id=self.location.identifier)
        product1 = products[0]
        products2 = plugin.get_available_products(
            location_id=self.location.identifier, current_products=[product1]
        )
        product2 = next(
            product
            for product in products2
            if product.identifier != product1.identifier
        )
        assert product1.amount == 1
        assert product2.amount == 1
        product1.amount = 2

        dates = plugin.get_dates(products=[product1, product2], location=self.location)

        self.assertGreater(len(dates), 0)
        self.assertIsInstance(dates[0], date)

        get_dates_request = self.cassette.requests[-1]
        self.assertIn(";numberOfCustomers=1", get_dates_request.uri)
