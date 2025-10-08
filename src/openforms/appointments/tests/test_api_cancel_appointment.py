from datetime import datetime

import pytz
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.data_removal.constants import RemovalMethods
from openforms.data_removal.tasks import delete_submissions
from openforms.forms.tests.factories import FormFactory
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..models import AppointmentsConfig
from ..tokens import submission_appointment_token_generator
from .factories import AppointmentFactory


class CancelAppointmentTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = AppointmentsConfig.get_solo()
        config.plugin = "demo"
        config.save()

    def setUp(self):
        super().setUp()
        self.addCleanup(AppointmentsConfig.clear_cache)

    def test_invalid_body_posted(self):
        appointment_info = AppointmentInfoFactory.create(registration_ok=True)
        submission = appointment_info.submission
        AppointmentFactory.create(submission=submission)
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:appointments-cancel",
            kwargs={"submission_uuid": submission.uuid},
        )

        response = self.client.post(endpoint, data={})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()["invalidParams"][0]
        self.assertEqual(error["name"], "email")
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "appointment_cancel_failure"
        )
        self.assertEqual(logs.count(), 1)

    def test_invalid_email_provided(self):
        appointment_info = AppointmentInfoFactory.create(registration_ok=True)
        submission = appointment_info.submission
        AppointmentFactory.create(
            submission=submission,
            contact_details_meta=[{"type": "email", "key": "email"}],
            contact_details={"email": "correct@example.com"},
        )
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:appointments-cancel",
            kwargs={"submission_uuid": submission.uuid},
        )

        response = self.client.post(endpoint, data={"email": "wrong@example.com"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "appointment_cancel_failure"
        )
        self.assertEqual(logs.count(), 1)

    def test_cancel_appointment_and_successful_submissions_pruning(self):
        with freeze_time("2021-07-20T12:00:00Z"):
            form = FormFactory.create(
                is_appointment=True,
                successful_submissions_removal_limit=2,
                successful_submissions_removal_method=(
                    RemovalMethods.delete_permanently
                ),
            )
            submission = SubmissionFactory.create(form=form, registration_success=True)
            AppointmentInfoFactory.create(
                submission=submission,
                registration_ok=True,
                start_time=datetime(2021, 7, 26, 12, 00, 00, tzinfo=pytz.UTC),
            )
            AppointmentFactory.create(
                submission=submission,
                datetime=datetime(2021, 7, 26, 12, 00, 00, tzinfo=pytz.UTC),
            )

            endpoint = reverse(
                "appointments:appointments-verify-cancel-appointment-link",
                kwargs={
                    "token": submission_appointment_token_generator.make_token(
                        submission
                    ),
                    "submission_uuid": submission.uuid,
                },
            )

        # appointment still valid, submission should not be deleted
        with freeze_time("2021-07-25T12:00:00Z"):
            self.assertEqual(Submission.objects.count(), 1)

            delete_submissions()

            self.assertTrue(Submission.objects.exists())

            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # appointment invalid, submission should be deleted
        with freeze_time("2021-07-27T12:00:00Z"):
            self.assertEqual(Submission.objects.count(), 1)

            delete_submissions()

            self.assertFalse(Submission.objects.exists())

            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_appointment_and_all_submissions_pruning(self):
        with freeze_time("2021-07-20T12:00:00Z"):
            form = FormFactory.create(
                is_appointment=True,
                all_submissions_removal_limit=2,
            )
            submission = SubmissionFactory.create(form=form)
            AppointmentInfoFactory.create(
                submission=submission,
                registration_ok=True,
                start_time=datetime(2021, 7, 26, 12, 00, 00, tzinfo=pytz.UTC),
            )
            AppointmentFactory.create(
                submission=submission,
                datetime=datetime(2021, 7, 26, 12, 00, 00, tzinfo=pytz.UTC),
            )

            endpoint = reverse(
                "appointments:appointments-verify-cancel-appointment-link",
                kwargs={
                    "token": submission_appointment_token_generator.make_token(
                        submission
                    ),
                    "submission_uuid": submission.uuid,
                },
            )

        # appointment still valid, submission should not be deleted
        with freeze_time("2021-07-25T12:00:00Z"):
            self.assertEqual(Submission.objects.count(), 1)

            delete_submissions()

            self.assertTrue(Submission.objects.exists())

            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # appointment invalid, submission should be deleted
        with freeze_time("2021-07-27T12:00:00Z"):
            self.assertEqual(Submission.objects.count(), 1)

            delete_submissions()

            self.assertFalse(Submission.objects.exists())

            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
