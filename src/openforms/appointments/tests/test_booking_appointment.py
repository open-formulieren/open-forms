import os
import sys
from datetime import UTC, datetime
from unittest.mock import patch

from django.test import TestCase

from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.tests.utils import supress_output

from ..base import CustomerDetails, Location, Product
from ..constants import AppointmentDetailsStatus
from ..contrib.demo.plugin import DemoAppointment
from ..core import book_for_submission
from ..exceptions import (
    AppointmentCreateFailed,
    AppointmentRegistrationFailed,
    NoAppointmentForm,
)
from ..models import AppointmentInfo
from ..registry import Registry
from .factories import AppointmentFactory, AppointmentProductFactory

register = Registry()
register("demo")(DemoAppointment)


@register("error")
class ErrorPlugin(DemoAppointment):
    def create_appointment(self, *args, **kwargs):
        raise AppointmentCreateFailed("nope")


class BookAppointmentTests(TestCase):
    def test_not_an_appointment_form(self):
        submission = SubmissionFactory.create()
        assert not submission.form.is_appointment

        with self.assertRaises(NoAppointmentForm):
            book_for_submission(submission)

        # no logs, no info created
        self.assertFalse(AppointmentInfo.objects.exists())
        self.assertFalse(TimelineLogProxy.objects.exists())

    def test_appointment_data_missing(self):
        submission = SubmissionFactory.create(form__is_appointment_form=True)
        assert submission.form.is_appointment

        with self.assertRaises(AppointmentRegistrationFailed):
            book_for_submission(submission)

        self.assertFalse(AppointmentInfo.objects.exists())
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/appointment_register_skip.txt"
            ).count(),
            1,
        )

    def test_creation_fails_logs_errors(self):
        submission = SubmissionFactory.create(form__is_appointment_form=True)
        AppointmentFactory.create(submission=submission, plugin="error")

        with patch("openforms.appointments.core.register", new=register):
            with self.assertRaises(AppointmentRegistrationFailed):
                book_for_submission(submission)

        with self.subTest("metadata registration"):
            info = AppointmentInfo.objects.get(submission=submission)
            self.assertEqual(info.status, AppointmentDetailsStatus.failed)
            self.assertGreater(len(info.error_information), 1)

        with self.subTest("Audit logging"):
            log_records = TimelineLogProxy.objects.all()
            self.assertEqual(len(log_records), 2)
            events = {lr.event for lr in log_records}
            self.assertEqual(
                events, {"appointment_register_start", "appointment_register_failure"}
            )

    def test_successful_creation(self):
        submission = SubmissionFactory.create(form__is_appointment_form=True)
        AppointmentFactory.create(submission=submission, plugin="demo")

        with patch("openforms.appointments.core.register", new=register):
            with supress_output(sys.stdout, os.devnull):
                appointment_id = book_for_submission(submission)

        self.assertEqual(appointment_id, "test 1")

        with self.subTest("metadata registration"):
            info = AppointmentInfo.objects.get(submission=submission)
            self.assertEqual(info.status, AppointmentDetailsStatus.success)
            self.assertEqual(info.error_information, "")
            self.assertEqual(info.appointment_id, "test 1")

        with self.subTest("Audit logging"):
            log_records = TimelineLogProxy.objects.all()
            self.assertEqual(len(log_records), 2)
            events = {lr.event for lr in log_records}
            self.assertEqual(
                events, {"appointment_register_start", "appointment_register_success"}
            )

    def test_plugin_invocation(self):
        submission = SubmissionFactory.create(form__is_appointment_form=True)
        start = datetime(2023, 8, 1, 12, 0, 15).replace(tzinfo=UTC)
        appointment = AppointmentFactory.create(
            submission=submission,
            plugin="demo",
            location="123",
            datetime=start,
            contact_details={
                "lastName": "English",
                "firstName": "Johny",
                "initials": "Johny",
            },
        )
        AppointmentProductFactory.create(
            appointment=appointment, product_id="456", amount=3
        )
        AppointmentProductFactory.create(
            appointment=appointment, product_id="789", amount=1
        )

        plugin = register["demo"]
        with (
            patch("openforms.appointments.core.register", new=register),
            patch.object(
                plugin, "create_appointment", return_value="ok"
            ) as mock_create,
        ):
            book_for_submission(submission)

        mock_create.assert_called_once_with(
            [
                Product(identifier="456", name="", amount=3),
                Product(identifier="789", name="", amount=1),
            ],
            Location(identifier="123", name=""),
            start,
            CustomerDetails(
                details={
                    "lastName": "English",
                    "firstName": "Johny",
                    "initials": "J.",
                }
            ),
            remarks="",
        )
