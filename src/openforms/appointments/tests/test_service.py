from unittest.mock import patch

from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ..service import register_appointment
from .factories import AppointmentInfoFactory


class RegisterAppointmentTests(TestCase):
    def test_no_appointment_registered_yet(self):
        submission = SubmissionFactory.create(completed=True)

        with patch(
            "openforms.appointments.utils.book_appointment_for_submission"
        ) as mock_book:
            register_appointment(submission)

        mock_book.assert_called_once_with(submission)

    def test_appointment_was_already_registered(self):
        appointment_info = AppointmentInfoFactory.create(
            submission__completed=True,
            registration_ok=True,
        )

        with patch(
            "openforms.appointments.utils.book_appointment_for_submission"
        ) as mock_book:
            register_appointment(appointment_info.submission)

        mock_book.assert_not_called()

    def test_previous_registration_failed(self):
        appointment_info = AppointmentInfoFactory.create(
            submission__completed=True,
            registration_failed=True,
        )

        with patch(
            "openforms.appointments.utils.book_appointment_for_submission"
        ) as mock_book:
            register_appointment(appointment_info.submission)

        mock_book.assert_called_once_with(appointment_info.submission)
