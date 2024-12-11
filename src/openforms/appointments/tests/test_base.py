from django.test import TestCase, override_settings
from django.urls import reverse

from openforms.submissions.tests.factories import SubmissionFactory

from ..registry import register
from ..tokens import submission_appointment_token_generator
from .factories import AppointmentInfoFactory


class BasePluginTests(TestCase):
    maxDiff = 1024

    @classmethod
    def setUpTestData(cls):
        # use demo plugin for tests
        cls.plugin = register["demo"]

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
