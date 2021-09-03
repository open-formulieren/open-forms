from datetime import datetime
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ...submissions.tests.factories import SubmissionFactory
from ..base import (
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)


class TestPlugin(BasePlugin):
    def get_appointment_details(self, identifier: str) -> str:
        return AppointmentDetails(
            identifier=identifier,
            products=[
                AppointmentProduct(identifier="1", name="Test product 1"),
                AppointmentProduct(identifier="2", name="Test product 2"),
            ],
            location=AppointmentLocation(identifier="1", name="Test location"),
            start_at=datetime(2021, 1, 1, 12, 0),
            end_at=datetime(2021, 1, 1, 12, 15),
            remarks="Remarks",
            other={"Some": "<h1>Data</h1>"},
        )


class BasePluginTests(TestCase):
    maxDiff = 1024

    @classmethod
    def setUpTestData(cls):
        cls.plugin = TestPlugin()

    def test_get_appointment_details_html(self):
        identifier = "1234567890"

        result = self.plugin.get_appointment_details_html(identifier)

        self.assertIn("Test product 1", result)
        self.assertIn("Test product 2", result)
        self.assertIn("Test location", result)
        self.assertIn("1 januari 2021, 12:00 - 12:15", result)
        self.assertIn("Remarks", result)
        self.assertIn("Some", result)
        self.assertIn("<h1>Data</h1>", result)

    @patch("openforms.appointments.base.submission_appointment_token_generator")
    def test_get_appointment_links_html(self, token_generator_mock):
        submission = SubmissionFactory.create()
        fake_token = "fake-token"

        token_generator_mock.make_token.return_value = fake_token

        result = self.plugin.get_appointment_links_html(submission)

        cancel_url = reverse(
            "api:appointments-verify-cancel-appointment-link",
            kwargs={"token": fake_token, "submission_id": submission.id},
        )

        self.assertIn(
            cancel_url,
            result,
        )
