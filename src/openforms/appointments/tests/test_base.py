from datetime import date, datetime

from django.test import TestCase, override_settings
from django.urls import reverse

from openforms.submissions.tests.factories import SubmissionFactory

from ..base import (
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)
from ..tokens import submission_appointment_token_generator
from .factories import AppointmentInfoFactory


class TestPlugin(BasePlugin):
    def get_available_products(self, current_products=None):
        return [
            AppointmentProduct(identifier="1", name="Test product 1"),
            AppointmentProduct(identifier="2", name="Test product 2"),
        ]

    def get_locations(self, products):
        return [AppointmentLocation(identifier="1", name="Test location")]

    def get_dates(self, products, location, start_at=None, end_at=None):
        return [date(2021, 1, 1)]

    def get_times(self, products, location, day):
        return [datetime(2021, 1, 1, 12, 0)]

    def create_appointment(self, products, location, start_at, client, remarks=None):
        return "1"

    def delete_appointment(self, identifier: str) -> None:
        return

    def get_appointment_details(self, identifier: str):
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
        cls.plugin = TestPlugin("base")

    @override_settings(BASE_URL="https://example.com/")
    def test_get_cancel_link(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(submission=submission, registration_ok=True)

        result = self.plugin.get_cancel_link(submission)

        cancel_path = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )
        cancel_url = f"https://example.com{cancel_path}"
        self.assertEqual(cancel_url, result)

    @override_settings(BASE_URL="https://example.com/")
    def test_get_change_link(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(submission=submission, registration_ok=True)

        result = self.plugin.get_change_link(submission)

        change_path = reverse(
            "appointments:appointments-verify-change-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )
        change_url = f"https://example.com{change_path}"
        self.assertEqual(change_url, result)
