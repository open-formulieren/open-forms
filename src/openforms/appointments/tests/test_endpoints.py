import uuid
from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from freezegun import freeze_time
from furl import furl

from openforms.config.models import GlobalConfiguration
from openforms.submissions.constants import SUBMISSIONS_SESSION_KEY
from openforms.submissions.tests.factories import SubmissionFactory

from ..tokens import submission_appointment_token_generator
from .factories import AppointmentInfoFactory


@freeze_time("2021-07-15T21:15:00Z")
class VerifyCancelAppointmentLinkViewTests(TestCase):
    def test_good_token_and_submission_redirect_and_add_submission_to_session(self):
        config = GlobalConfiguration.get_solo()
        config.cancel_appointment_page = "http://maykinmedia.nl/afspraak-annuleren"
        config.save()

        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # one day after token generation
        with freeze_time("2021-07-16T21:15:00Z"):
            response = self.client.get(endpoint)

        expected_redirect_url = (
            furl("http://maykinmedia.nl/afspraak-annuleren")
            .add(
                {
                    "time": "2021-07-21T12:00:00+00:00",
                    "submission_uuid": submission.uuid,
                }
            )
            .url
        )
        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )
        # Assert submission is stored in session
        self.assertIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

    def test_runtime_error_raised_when_no_cancel_appointment_page_is_specified(self):
        config = GlobalConfiguration.get_solo()
        config.cancel_appointment_page = ""
        config.save()

        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with self.assertRaises(RuntimeError):
            self.client.get(endpoint)

    def test_403_response_with_unfound_submission(self):
        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "irrelevant",
                "submission_uuid": uuid.uuid4(),
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_403_response_with_bad_token(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "bad",
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_invalid_after_appointment_time(self):
        config = GlobalConfiguration.get_solo()
        config.cancel_appointment_page = "http://maykinmedia.nl/afspraak-annuleren"
        config.save()
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with freeze_time("2021-07-22T12:00:00Z"):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_valid_on_same_day_appointment(self):
        config = GlobalConfiguration.get_solo()
        config.cancel_appointment_page = "http://maykinmedia.nl/afspraak-annuleren"
        config.save()
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with freeze_time("2021-07-21T11:59:59Z"):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 302)
