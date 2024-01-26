"""
Tests for retrieving available products from Qmatic through our own API.
"""

from django.test import TestCase

from openforms.utils.tests.vcr import OFVCRMixin

from ....base import Product
from ..plugin import QmaticAppointment
from .utils import TEST_FILES, MockConfigMixin

QMATIC_BASE_URL = "http://localhost:8080/qmatic/calendar-backend/public/api/"

plugin = QmaticAppointment("qmatic")


def _get_location(index: int = 0):
    locations = plugin.get_locations()
    assert len(locations) > 1
    return locations[index]


class ListAvailableProductsTests(OFVCRMixin, MockConfigMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # update the dummy service to point to the real service API root
        cls.service.api_root = QMATIC_BASE_URL
        cls.service.save()

    def test_listing_products_without_other_product_constraint(self):
        """
        Test that with/without location filter produces different amounts of products.
        """
        num_unfiltered_products = 0
        location = _get_location(-1)  # can't pickle this if a subtest fails

        with self.subTest("List of unfiltered products"):
            products = plugin.get_available_products()

            num_unfiltered_products = len(products)
            self.assertGreater(num_unfiltered_products, 0)

        with self.subTest("Filter products by location"):
            filtered_products = plugin.get_available_products(
                location_id=location.identifier
            )

            self.assertLess(len(filtered_products), num_unfiltered_products)

    def test_listing_products_with_location_and_product_constraint(self):
        location = _get_location()

        all_location_products = plugin.get_available_products(
            location_id=location.identifier
        )
        num_location_products = len(all_location_products)
        self.assertGreater(num_location_products, 1)

        # now grab a product and use that as constraint
        product = Product(identifier=all_location_products[0].identifier, name="")

        available_products = plugin.get_available_products(
            location_id=location.identifier, current_products=[product]
        )

        self.assertLess(len(available_products), num_location_products)

    def test_listing_products_without_location_with_product_constraint(self):
        all_products = plugin.get_available_products()
        num_location_products = len(all_products)
        self.assertGreater(num_location_products, 1)

        # now grab a product and use that as constraint
        product = Product(identifier=all_products[0].identifier, name="")

        available_products = plugin.get_available_products(current_products=[product])

        self.assertLess(len(available_products), num_location_products)
