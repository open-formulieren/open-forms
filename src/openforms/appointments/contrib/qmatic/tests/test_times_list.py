"""
Tests for retrieving available appointment times from Qmatic through our own API.
"""

from datetime import date

from django.test import TestCase

from openforms.utils.tests.vcr import OFVCRMixin

from ..plugin import QmaticAppointment
from .utils import TEST_FILES, MockConfigMixin

QMATIC_BASE_URL = "http://localhost:8080/qmatic/calendar-backend/public/api/"

# The test date below should return actual results when querying for times. So if you
# need to re-generate the cassettes, pick a week day in the future!
TEST_DATE = date(2023, 10, 23)

plugin = QmaticAppointment("qmatic")


class ListAvailableTimesTests(OFVCRMixin, MockConfigMixin, TestCase):
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

    def test_listing_times_single_product_single_customer(self):
        products = plugin.get_available_products(location_id=self.location.identifier)
        product = next(
            product for product in products if product.identifier == "Identiteitskaart"
        )
        assert product.amount == 1

        times = plugin.get_times(
            products=[product], location=self.location, day=TEST_DATE
        )

        self.assertGreater(len(times), 0)
        self.assertIsInstance(times[0], date)

    def test_listing_times_single_product_multiple_customers(self):
        products = plugin.get_available_products(location_id=self.location.identifier)
        product = next(
            product for product in products if product.identifier == "Identiteitskaart"
        )
        product.amount = 999  # amount that should not return any times

        with self.subTest("product.amount set"):
            times = plugin.get_times(
                products=[product], location=self.location, day=TEST_DATE
            )

            self.assertEqual(len(times), 0)

        with self.subTest("product repeated"):
            product.amount = 1
            times = plugin.get_times(
                products=[product] * 999, location=self.location, day=TEST_DATE
            )

            self.assertEqual(len(times), 0)

    def test_multiple_products_multiple_customers(self):
        products = plugin.get_available_products(location_id=self.location.identifier)
        product1 = next(
            product for product in products if product.identifier == "Identiteitskaart"
        )
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

        times = plugin.get_times(
            products=[product1, product2], location=self.location, day=TEST_DATE
        )

        self.assertGreater(len(times), 0)
        self.assertIsInstance(times[0], date)

        get_times_request = self.cassette.requests[-1]
        self.assertIn(";numberOfCustomers=1", get_times_request.uri)
