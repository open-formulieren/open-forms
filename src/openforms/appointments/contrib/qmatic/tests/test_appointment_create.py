"""
VCR tests for creating an appointment with Qmatic.
"""

import json
from datetime import date

from django.test import TestCase

from openforms.utils.tests.vcr import OFVCRMixin

from ..constants import CustomerFields
from ..plugin import QmaticAppointment, _CustomerDetails
from .utils import TEST_FILES, MockConfigMixin

QMATIC_BASE_URL = "http://localhost:8080/qmatic/calendar-backend/public/api/"

# The test date below should return actual results when querying for times. So if you
# need to re-generate the cassettes, pick a week day in the future!
TEST_DATE = date(2023, 10, 23)

plugin = QmaticAppointment("qmatic")


def scrub_cookies(response: dict):
    if "Set-Cookie" in response["headers"]:
        del response["headers"]["Set-Cookie"]
    return response


class CreateAppointmentTests(OFVCRMixin, MockConfigMixin, TestCase):
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

    def _get_vcr_kwargs(self, **kwargs):
        kwargs.update(
            {
                "decode_compressed_response": False,
                "before_record_response": scrub_cookies,
            }
        )
        return super()._get_vcr_kwargs(**kwargs)

    def test_create_appointment_single_product_single_customer(self):
        customer = _CustomerDetails(
            details={
                CustomerFields.email: "automated-test@example.com",
                CustomerFields.last_name: "TEST (automated)",
            }
        )
        products = plugin.get_available_products(location_id=self.location.identifier)
        product = next(
            product for product in products if product.identifier == "Identiteitskaart"
        )
        assert product.amount == 1
        times = plugin.get_times(
            products=[product], location=self.location, day=TEST_DATE
        )

        appointment_id = plugin.create_appointment(
            products=[product],
            location=self.location,
            start_at=times[0],
            client=customer,
            remarks="AUTOMATED TEST APPOINTMENT - can safely be removed.",
        )

        self.assertTrue(bool(appointment_id))

        # and cancel it again to clean up after ourselves
        plugin.delete_appointment(appointment_id)

    def test_create_appointment_multi_product_multi_customer(self):
        customer = _CustomerDetails(
            details={
                CustomerFields.email: "automated-test@example.com",
                CustomerFields.last_name: "TEST (automated)",
            }
        )
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
        products = [product1, product2]

        times = plugin.get_times(
            products=products, location=self.location, day=TEST_DATE
        )

        appointment_id = plugin.create_appointment(
            products=products,
            location=self.location,
            start_at=times[0],
            client=customer,
            remarks="AUTOMATED TEST APPOINTMENT - can safely be removed.",
        )

        self.assertTrue(bool(appointment_id))

        # and cancel it again to clean up after ourselves
        plugin.delete_appointment(appointment_id)

        create_request = self.cassette.requests[-2]
        self.assertEqual(create_request.method, "POST")
        request_data = json.loads(create_request.body.decode("utf-8"))
        self.assertEqual(len(request_data["customers"]), 2)
        self.assertEqual(len(request_data["services"]), 2)
