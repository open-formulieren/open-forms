from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.mixins import SubmissionsMixin

from ..models import AppointmentsConfig
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
