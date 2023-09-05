"""
Tests for retrieving available products from Qmatic through our own API.
"""
import os
from pathlib import Path

from django.test import TestCase

from vcr.unittest import VCRMixin

from ..plugin import QmaticAppointment
from .utils import MockConfigMixin

TEST_FILES = Path(__file__).parent.resolve() / "data"

QMATIC_BASE_URL = "http://localhost:8080/qmatic/calendar-backend/public/api/"

# https://vcrpy.readthedocs.io/en/latest/usage.html#record-modes
# once in dev, none in CI
RECORD_MODE = os.environ.get("VCR_RECORD_MODE", "once")


plugin = QmaticAppointment("qmatic")


class QmaticVCRMixin(VCRMixin):
    def _get_cassette_library_dir(self):
        return str(TEST_FILES / "vcr_cassettes" / self.__class__.__qualname__)

    def _get_vcr_kwargs(self):
        kwargs = super()._get_vcr_kwargs()
        kwargs["record_mode"] = RECORD_MODE
        return kwargs


class ListAvailableProductsTests(QmaticVCRMixin, MockConfigMixin, TestCase):
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

        with self.subTest("List of unfiltered products"):
            products = plugin.get_available_products()

            num_unfiltered_products = len(products)
            self.assertGreater(num_unfiltered_products, 0)

        with self.subTest("Filter products by location"):
            locations = plugin.get_locations()
            assert len(locations) > 1

            filtered_products = plugin.get_available_products(
                location_id=locations[0].identifier
            )
            self.assertLess(len(filtered_products), num_unfiltered_products)
