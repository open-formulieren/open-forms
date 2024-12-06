"""
Test that the demo plugin can be used to simulate endpoint responses.
"""

from datetime import date
from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..plugin import DemoAppointment


class DemoPluginTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submission = SubmissionFactory.create()
        cls.plugin = DemoAppointment("demo")

    def setUp(self):
        super().setUp()

        self._add_submission_to_session(self.submission)

        patcher = patch(
            "openforms.appointments.api.views.get_plugin", return_value=self.plugin
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_product_list(self):
        endpoint = reverse("api:appointments-products-list")

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products = response.json()
        self.assertEqual(len(products), 2)

    def test_location_list(self):
        endpoint = reverse("api:appointments-locations-list")

        response = self.client.get(endpoint, {"product_id": "2"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        locations = response.json()
        self.assertEqual(len(locations), 1)

    def test_dates_list(self):
        endpoint = reverse("api:appointments-dates-list")

        response = self.client.get(endpoint, {"product_id": "2", "location_id": "1"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dates = response.json()
        self.assertEqual(len(dates), 1)

    def test_times_list(self):
        endpoint = reverse("api:appointments-times-list")

        response = self.client.get(
            endpoint,
            {"product_id": "2", "location_id": "1", "date": date.today().isoformat()},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        times = response.json()
        self.assertEqual(len(times), 4)

    def test_required_customer_fields_list(self):
        endpoint = reverse("api:appointments-customer-fields")

        response = self.client.get(endpoint, {"product_id": "2"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        components = response.json()
        self.assertEqual(len(components), 2)
