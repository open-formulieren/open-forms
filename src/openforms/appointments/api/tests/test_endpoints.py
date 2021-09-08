import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode

from openforms.config.models import GlobalConfiguration
from openforms.submissions.constants import SUBMISSIONS_SESSION_KEY
from openforms.submissions.tests.factories import SubmissionFactory

from ...tests.factories import AppointmentInfoFactory


class VerifyCancelAppointmentLinkViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        config = GlobalConfiguration.get_solo()
        config.cancel_appointment_page = "http://maykinmedia.nl/afspraak-annuleren"
        config.save()

    @patch(
        "openforms.appointments.api.views.submission_appointment_token_generator.check_token",
        return_value=True,
    )
    def test_good_token_and_submission_redirect_and_add_submission_to_session(
        self, check_token_mock
    ):
        submission = SubmissionFactory.create()
        AppointmentInfoFactory.create(
            submission=submission,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "api:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "mocked",
                "base64_submission_uuid": urlsafe_base64_encode(
                    str(submission.uuid).encode()
                ),
            },
        )

        response = self.client.get(endpoint)

        # Assert submission is stored in session
        self.assertEqual(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY][0]
        )

        expected_redirect_url = (
            f"http://maykinmedia.nl/afspraak-annuleren?"
            f"time=2021-07-21T12%3A00%3A00+00%3A00&submission_uuid={str(submission.uuid)}"
        )
        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )

    def test_404_response_with_unfound_submission(self):
        endpoint = reverse(
            "api:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "mocked",
                "base64_submission_uuid": urlsafe_base64_encode(
                    str(uuid.uuid4()).encode()
                ),
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    @patch(
        "openforms.appointments.api.views.submission_appointment_token_generator.check_token",
        return_value=False,
    )
    def test_403_response_with_bad_token(self, check_token_mock):
        submission = SubmissionFactory.create()

        endpoint = reverse(
            "api:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "bad",
                "base64_submission_uuid": urlsafe_base64_encode(
                    str(submission.uuid).encode()
                ),
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)
