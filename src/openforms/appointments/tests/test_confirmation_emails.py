"""
Test the generic confirmation e-mail sending for appointment forms.
"""
from datetime import date, datetime, time
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from openforms.config.models import GlobalConfiguration
from openforms.formio.typing import Component
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.utils import send_confirmation_email

from ..base import AppointmentDetails, BasePlugin, Location, Product
from ..registry import Registry
from .factories import AppointmentFactory

register = Registry()

LAST_NAME: Component = {
    "type": "textfield",
    "key": "lastName",
    "label": "Last name",
    "validate": {
        "required": True,
        "maxLength": 20,
    },
}

EMAIL: Component = {
    "type": "email",
    "key": "email",
    "label": "Email",
    "validate": {
        "required": True,
    },
}


@register("no-email")
class NoEmailPlugin(BasePlugin):
    def get_available_products(self, *args, **kwargs) -> list[Product]:
        return [Product(identifier="dummy", name="Dummy")]

    def get_locations(self, *args, **kwargs) -> list[Location]:
        return [Location(identifier="dummy", name="Knowhere")]

    def get_dates(self, *args, **kwargs):
        return [date(2023, 8, 1)]

    def get_times(self, *args, **kwargs):
        return [
            datetime.combine(day, time(12, 0), tzinfo=timezone.utc)
            for day in self.get_dates()
        ]

    def get_required_customer_fields(self, *args, **kwargs) -> list[Component]:
        return [LAST_NAME]

    def create_appointment(self, *args, **kwargs):
        return "dummy-identifier"

    def delete_appointment(self, *args, **kwargs):
        pass

    def get_appointment_details(self, identifier: str) -> AppointmentDetails:
        return AppointmentDetails(
            identifier=identifier,
            products=[Product(identifier="dummy", name="Dummy")],
            location=Location(
                identifier="dummy",
                name="Knowhere",
                city="Teststad",
                postalcode="1234AB",
            ),
            start_at=datetime(2023, 8, 1, 12, 0).replace(tzinfo=timezone.utc),
            end_at=datetime(2023, 8, 1, 12, 15).replace(tzinfo=timezone.utc),
            remarks="Remarks",
            other={"Some": "<h1>Data</h1>"},
        )


@register("with-email")
class WithEmailPlugin(NoEmailPlugin):
    def get_required_customer_fields(self, *args, **kwargs) -> list[Component]:
        return [LAST_NAME, EMAIL]


class AppointmentCreationConfirmationMailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.config = GlobalConfiguration(
            confirmation_email_content="{% summary %}\n{% appointment_information %}",
            confirmation_email_subject="CONFIRMATION",
        )

    def setUp(self):
        super().setUp()

        patcher = patch(
            "openforms.emails.confirmation_emails.GlobalConfiguration.get_solo",
            return_value=self.config,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        registry_patcher = patch("openforms.appointments.utils.register", new=register)
        registry_patcher.start()
        self.addCleanup(registry_patcher.stop)

    def test_send_confirmation_mail_disabled(self):
        appointment = AppointmentFactory.create(
            submission__form__is_appointment_form=True,
            submission__form__send_confirmation_email=False,
            products=[Product(identifier="dummy", name="")],
            appointment_info__registration_ok=True,
            contact_details_meta=[LAST_NAME, EMAIL],
            contact_details={"lastName": "Powers", "email": "austin@powers.net"},
        )

        send_confirmation_email(appointment.submission)

        self.assertEqual(len(mail.outbox), 0)

    def test_no_available_email_address(self):
        appointment = AppointmentFactory.create(
            plugin="no-email",
            submission__form__is_appointment_form=True,
            submission__form__send_confirmation_email=True,
            products=[Product(identifier="dummy", name="")],
            appointment_info__registration_ok=True,
            contact_details_meta=[LAST_NAME],
            contact_details={"lastName": "Powers"},
        )

        send_confirmation_email(appointment.submission)

        self.assertEqual(len(mail.outbox), 0)

    def test_no_crash_on_missing_appointment_details(self):
        submission = SubmissionFactory.create(
            form__is_appointment_form=True,
            form__send_confirmation_email=True,
        )
        assert not hasattr(submission, "appointment")

        send_confirmation_email(submission)

        self.assertEqual(len(mail.outbox), 0)

    def test_bad_data(self):
        appointment = AppointmentFactory.create(
            plugin="with-email",
            submission__form__is_appointment_form=True,
            submission__form__send_confirmation_email=True,
            products=[Product(identifier="dummy", name="")],
            appointment_info__registration_ok=True,
            contact_details_meta=[LAST_NAME, EMAIL],
            contact_details={"lastName": "Powers", "email": 123},
        )

        with self.assertRaises(TypeError):
            send_confirmation_email(appointment.submission)

    def test_confirmation_email_goes_to_correct_recipients(self):
        appointment = AppointmentFactory.create(
            plugin="with-email",
            submission__form__is_appointment_form=True,
            submission__form__send_confirmation_email=True,
            products=[Product(identifier="dummy", name="")],
            appointment_info__registration_ok=True,
            contact_details_meta=[LAST_NAME, EMAIL],
            contact_details={"lastName": "Powers", "email": "austin@powers.net"},
        )

        send_confirmation_email(appointment.submission)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "CONFIRMATION")
        self.assertEqual(message.recipients(), ["austin@powers.net"])
