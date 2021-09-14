import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from furl import furl

from openforms.config.models import GlobalConfiguration
from openforms.submissions.constants import SUBMISSIONS_SESSION_KEY
from openforms.submissions.tests.factories import SubmissionFactory

from .factories import AppointmentInfoFactory


class VerifyCancelAppointmentLinkViewTests(TestCase):
    @patch(
        "openforms.appointments.views.submission_appointment_token_generator.check_token",
        return_value=True,
    )
    def test_good_token_and_submission_redirect_and_add_submission_to_session(
        self, check_token_mock
    ):
        config = GlobalConfiguration.get_solo()
        config.cancel_appointment_page = "http://maykinmedia.nl/afspraak-annuleren"
        config.save()

        submission = SubmissionFactory.create()
        AppointmentInfoFactory.create(
            submission=submission,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "mocked",
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        # Assert submission is stored in session
        self.assertIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

        expected_redirect_url = (
            furl(config.cancel_appointment_page)
            .add(
                {
                    "time": submission.appointment_info.start_time.isoformat(),
                    "submission_uuid": submission.uuid,
                }
            )
            .url
        )

        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )

    @patch(
        "openforms.appointments.views.submission_appointment_token_generator.check_token",
        return_value=True,
    )
    def test_runtime_error_raised_when_no_cancel_appointment_page_is_specified(
        self, check_token_mock
    ):
        config = GlobalConfiguration.get_solo()
        config.cancel_appointment_page = ""
        config.save()

        submission = SubmissionFactory.create()
        AppointmentInfoFactory.create(
            submission=submission,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "mocked",
                "submission_uuid": submission.uuid,
            },
        )

        with self.assertRaises(RuntimeError):
            self.client.get(endpoint)

    def test_403_response_with_unfound_submission(self):
        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "mocked",
                "submission_uuid": uuid.uuid4(),
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    @patch(
        "openforms.appointments.views.submission_appointment_token_generator.check_token",
        return_value=False,
    )
    def test_403_response_with_bad_token(self, check_token_mock):
        submission = SubmissionFactory.create()

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "bad",
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)
