from unittest.mock import patch

from django.test import TestCase

from ..exceptions import AppointmentRegistrationFailed
from ..tasks import maybe_register_appointment
from .factories import AppointmentInfoFactory, SubmissionFactory


class AppointmentRegistrationTaskTests(TestCase):
    def test_happy_flow(self):
        submission = SubmissionFactory.create(completed=True)

        with patch(
            "openforms.appointments.tasks.book_appointment_for_submission"
        ) as mock_book:
            maybe_register_appointment(submission.id)

        mock_book.assert_called_once()

        submission.refresh_from_db()
        self.assertFalse(submission.needs_on_completion_retry)

    def test_appointment_registration_fails(self):
        submission = SubmissionFactory.create(completed=True)

        with patch(
            "openforms.appointments.tasks.book_appointment_for_submission"
        ) as mock_book:
            mock_book.side_effect = AppointmentRegistrationFailed("Failed")
            with self.assertRaises(AppointmentRegistrationFailed):
                maybe_register_appointment(submission.id)

        mock_book.assert_called_once()

        submission.refresh_from_db()
        # NO automatic retry - user gets feedback and needs to correct/retry
        self.assertFalse(submission.needs_on_completion_retry)

    def test_no_appointment_registered_yet(self):
        submission = SubmissionFactory.create(completed=True)

        with patch(
            "openforms.appointments.tasks.book_appointment_for_submission"
        ) as mock_book:
            maybe_register_appointment(submission.id)

        mock_book.assert_called_once_with(submission)

    def test_appointment_was_already_registered(self):
        appointment_info = AppointmentInfoFactory.create(
            submission__completed=True,
            registration_ok=True,
        )

        with patch(
            "openforms.appointments.tasks.book_appointment_for_submission"
        ) as mock_book:
            maybe_register_appointment(appointment_info.submission.id)

        mock_book.assert_not_called()

    def test_previous_registration_failed(self):
        appointment_info = AppointmentInfoFactory.create(
            submission__completed=True,
            registration_failed=True,
        )

        with patch(
            "openforms.appointments.tasks.book_appointment_for_submission"
        ) as mock_book:
            maybe_register_appointment(appointment_info.submission.id)

        mock_book.assert_called_once_with(appointment_info.submission)
