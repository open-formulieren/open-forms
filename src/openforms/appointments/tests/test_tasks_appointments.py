from unittest.mock import patch

from django.test import TestCase

from ..exceptions import AppointmentRegistrationFailed
from ..tasks import maybe_register_appointment
from .factories import SubmissionFactory


class AppointmentRegistrationTaskTests(TestCase):
    def test_happy_flow(self):
        submission = SubmissionFactory.create(completed=True)

        with patch(
            "openforms.appointments.tasks.register_appointment"
        ) as mock_register:
            maybe_register_appointment(submission.id)

        mock_register.assert_called_once()

        submission.refresh_from_db()
        self.assertFalse(submission.needs_on_completion_retry)

    def test_appointment_registration_fails(self):
        submission = SubmissionFactory.create(completed=True)

        with patch(
            "openforms.appointments.tasks.register_appointment"
        ) as mock_register:
            mock_register.side_effect = AppointmentRegistrationFailed("Failed")
            with self.assertRaises(AppointmentRegistrationFailed):
                maybe_register_appointment(submission.id)

        mock_register.assert_called_once()

        submission.refresh_from_db()
        # NO automatic retry - user gets feedback and needs to correct/retry
        self.assertFalse(submission.needs_on_completion_retry)
