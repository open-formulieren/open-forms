from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from privates.test import temp_private_root

from openforms.appointments.constants import AppointmentDetailsStatus
from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.appointments.tests.test_base import TestPlugin
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory

from ..tasks import maybe_send_confirmation_email
from .factories import SubmissionFactory, SubmissionStepFactory


@temp_private_root()
class ConfirmationEmailTests(TestCase):
    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    def test_completed_submission_send_confirmation_email(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
        )
        # add a second step
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form=submission.form,
            form_step__optional=False,
            data={"foo": "bar"},
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )

        # "execute" the celery task
        maybe_send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, "Confirmation mail")
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["test@test.nl"])

        # Check that the template is used
        self.assertIn('<table border="0">', message.body)
        self.assertIn("Information filled in: bar", message.body)

    def test_complete_submission_without_email_recipient(self):
        submission = SubmissionFactory.create(completed=True)
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )

        # "execute" the celery task
        maybe_send_confirmation_email(submission.id)

        # assert that no e-mail was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_complete_submission_send_confirmation_email_with_summary(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {"key": "email", "confirmationRecipient": True, "label": "Email"},
                {"key": "foo", "showInEmail": True, "label": "Foo"},
            ],
            submitted_data={"foo": "foovalue", "email": "test@test.nl"},
        )
        # add second step
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form=submission.form,
            form_step__form_definition__configuration={
                "components": [
                    {"key": "bar", "label": "Bar", "showInEmail": True},
                    {"key": "hello", "label": "Hello", "showInEmail": False},
                ],
            },
            data={"bar": "barvalue", "hello": "hellovalue"},
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation mail",
            content="Information filled in: {{ foo }}, {{ bar }} and {{ hello }}. Submission summary: {% summary %}",
        )

        # "execute" the celery task
        maybe_send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(
            "Information filled in: foovalue, barvalue and hellovalue.", message.body
        )
        self.assertIn("<th>Bar</th>", message.body)
        self.assertIn("<th>barvalue</th>", message.body)
        self.assertIn("<th>Foo</th>", message.body)
        self.assertIn("<th>foovalue</th>", message.body)
        self.assertNotIn("<th>Hello</th>", message.body)
        self.assertNotIn("<th>hellovalue</th>", message.body)

    def test_complete_submission_send_confirmation_email_to_many_recipients(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "single1",
                    "type": "email",
                    "label": "One",
                    "confirmationRecipient": True,
                },
                {
                    "key": "single2",
                    "type": "email",
                    "label": "Two",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"single1": "single1@test.nl", "single2": "single2@test.nl"},
        )
        # second step
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form=submission.form,
            form_step__form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "many",
                        "type": "email",
                        "label": "Many",
                        "multiple": True,
                        "confirmationRecipient": True,
                    },
                ],
            },
            data={"many": ["many1@test.nl", "many2@test.nl"]},
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )

        # "execute" the celery task
        maybe_send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(
            set(message.to),
            {"single1@test.nl", "single2@test.nl", "many1@test.nl", "many2@test.nl"},
        )

    # TODO: this should instead use a client from registry configured on the form,
    # and then we can just specify the client to use in the SubmissionFactory rather
    # than having the monkeypatch
    @patch("openforms.submissions.utils.get_client", return_value=TestPlugin())
    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    def test_complete_submission_send_confirmation_email_with_appointment_details(
        self, mock_get_client
    ):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation mail",
            content="Confirmation mail content",
        )
        AppointmentInfoFactory.create(
            status=AppointmentDetailsStatus.success,
            appointment_id="123456789",
            submission=submission,
        )

        # "execute" the celery task
        maybe_send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Confirmation mail")
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["test@test.nl"])

        # Check that appointment information is in email
        self.assertIn("Confirmation mail content", message.body)
        self.assertIn('<table border="0">', message.body)
        self.assertIn("Confirmation mail content", message.body)
        self.assertIn("Test product 1", message.body)
        self.assertIn("Test product 2", message.body)
        self.assertIn("Test location", message.body)
        self.assertIn("1 januari 2021, 12:00 - 12:15", message.body)
        self.assertIn("Remarks", message.body)
        self.assertIn("Some", message.body)
        self.assertIn("<h1>Data</h1>", message.body)
