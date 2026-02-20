"""
Test the generic confirmation e-mail sending for appointment forms.
"""

from datetime import UTC, date, datetime, time
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils.html import escape
from django.utils.translation import gettext as _

from openforms.config.models import GlobalConfiguration
from openforms.formio.typing import Component
from openforms.submissions.tasks import schedule_emails
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.utils import send_confirmation_email
from openforms.utils.tests.html_assert import HTMLAssertMixin

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
    "showInEmail": True,
}

EMAIL: Component = {
    "type": "email",
    "key": "email",
    "label": "Email",
    "validate": {
        "required": True,
    },
    "showInEmail": True,
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
            datetime.combine(day, time(12, 0), tzinfo=UTC) for day in self.get_dates()
        ]

    def get_required_customer_fields(
        self, *args, **kwargs
    ) -> tuple[list[Component], None]:
        return [LAST_NAME], None

    def create_appointment(self, *args, **kwargs):
        return "dummy-identifier"

    def delete_appointment(self, *args, **kwargs):
        pass

    def get_appointment_details(self, identifier: str) -> AppointmentDetails:
        return AppointmentDetails(
            identifier=identifier,
            products=[Product(identifier="dummy", name="Dummy", amount=2)],
            location=Location(
                identifier="dummy",
                name="Knowhere",
                city="Teststad",
                postalcode="1234AB",
            ),
            start_at=datetime(2023, 8, 1, 12, 0).replace(tzinfo=UTC),
            end_at=datetime(2023, 8, 1, 12, 15).replace(tzinfo=UTC),
            remarks="Remarks",
            other={"Some": "<h1>Data</h1>"},
        )


@register("with-email")
class WithEmailPlugin(NoEmailPlugin):
    def get_required_customer_fields(
        self, *args, **kwargs
    ) -> tuple[list[Component], None]:
        return [LAST_NAME, EMAIL], None


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AppointmentCreationConfirmationMailTests(HTMLAssertMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.config = GlobalConfiguration(
            confirmation_email_content="{% confirmation_summary %}\n{% appointment_information %}",
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

        schedule_emails(appointment.submission.id)

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

    def test_appointment_data_present_in_confirmation_email(self):
        appointment = AppointmentFactory.create(
            plugin="with-email",
            submission__language_code="nl",
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

        message_text = message.body
        message_html = message.alternatives[0][0]  # type: ignore
        assert isinstance(message_html, str)

        with self.subTest("Product name", type="plain text"):
            self.assertIn("Dummy (x2)", message_text)

        with self.subTest("Location name", type="plain text"):
            self.assertIn("Knowhere", message_text)
            self.assertIn("Teststad", message_text)
            self.assertIn("1234AB", message_text)

        with self.subTest("Appointment date and time", type="plain text"):
            self.assertIn("1 augustus 2023, 14:00 - 14:15", message_text)

        with self.subTest("Remarks", type="plain text"):
            self.assertIn("Remarks", message_text)

        with self.subTest("Additional data", type="plain text"):
            self.assertIn("Some:\nData", message_text)

        with self.subTest("No generic summary data", type="plain text"):
            self.assertNotIn(_("Summary"), message_text)

        with self.subTest("Contact details", type="plain text"):
            self.assertIn("Last name: Powers", message_text)
            self.assertIn("Email: austin@powers.net", message_text)

        with self.subTest("Product name", type="HTML"):
            self.assertTagWithTextIn("td", "Dummy (x2)", message_html)

        with self.subTest("Location name", type="HTML"):
            self.assertIn("Knowhere", message_html)
            self.assertIn("Teststad", message_html)
            self.assertIn("1234AB", message_html)

        with self.subTest("Appointment date and time", type="HTML"):
            self.assertTagWithTextIn(
                "td", "1 augustus 2023, 14:00 - 14:15", message_html
            )

        with self.subTest("Remarks", type="HTML"):
            self.assertTagWithTextIn("td", "Remarks", message_html)

        with self.subTest("Additional data", type="HTML"):
            self.assertTagWithTextIn("td", "Some", message_html)
            self.assertTagWithTextIn(
                "td",
                escape("<h1>Data</h1>"),
                message_html,
            )

        with self.subTest("No generic summary data", type="HTML"):
            self.assertNotIn(_("Summary"), message_html)

        with self.subTest("Contact details", type="HTML"):
            self.assertTagWithTextIn("td", "Last name", message_html)
            self.assertTagWithTextIn("td", "Powers", message_html)
            self.assertTagWithTextIn("td", "Email", message_html)
            self.assertTagWithTextIn("td", "austin@powers.net", message_html)

    def test_cancel_instructions(self):
        appointment = AppointmentFactory.create(
            plugin="with-email",
            submission__language_code="nl",
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

        message_text = message.body
        message_html = message.alternatives[0][0]  # type: ignore
        assert isinstance(message_html, str)

        plugin = register["with-email"]
        cancel_link = plugin.get_cancel_link(appointment.submission)

        with self.subTest(type="HTML"):
            self.assertIn(cancel_link, message_html)

        with self.subTest(type="plain text"):
            self.assertIn(cancel_link, message_text)
