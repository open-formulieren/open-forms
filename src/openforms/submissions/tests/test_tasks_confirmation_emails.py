from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from privates.test import temp_private_root

from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory

from ..tasks import maybe_send_confirmation_email
from ..tasks.emails import send_confirmation_email_after_payment_timeout
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

        # Check status is updated
        submission.refresh_from_db()
        self.assertTrue(submission.confirmation_email_sent)

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

        # Check status
        submission.refresh_from_db()
        self.assertFalse(submission.confirmation_email_sent)

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

    @override_settings(
        DEFAULT_FROM_EMAIL="info@open-forms.nl",
        PAYMENT_CONFIRMATION_EMAIL_TIMEOUT=1200,
    )
    def test_completed_submission_with_incomplete_payment_delays_confirmation_email(
        self,
    ):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
        )
        ConfirmationEmailTemplateFactory.create(form=submission.form, content="test")
        self.assertTrue(submission.payment_required)

        with patch.object(
            send_confirmation_email_after_payment_timeout, "apply_async"
        ) as mock_apply_async:
            # "execute" the celery task
            maybe_send_confirmation_email(submission.id)

            # verify timeout task is delayed
            mock_apply_async.assert_called_once_with(
                args=(submission.id,), countdown=1200
            )

    def test_completed_submission_after_timeout_with_send_email(
        self,
    ):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
        )
        ConfirmationEmailTemplateFactory.create(form=submission.form, content="test")

        # "execute" the celery task
        send_confirmation_email_after_payment_timeout(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(
        DEFAULT_FROM_EMAIL="info@open-forms.nl",
        PAYMENT_CONFIRMATION_EMAIL_TIMEOUT=1200,
    )
    def test_completed_submission_with_confirmation_email_when_already_sent(
        self,
    ):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
            # mark as already sent
            confirmation_email_sent=True,
        )
        ConfirmationEmailTemplateFactory.create(form=submission.form, content="test")

        # "execute" the celery task
        maybe_send_confirmation_email(submission.id)

        # assert that no e-mail was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_completed_submission_after_timeout_with_confirmation_email_when_already_sent(
        self,
    ):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
            # mark as already sent
            confirmation_email_sent=True,
        )
        ConfirmationEmailTemplateFactory.create(form=submission.form, content="test")

        # "execute" the celery task
        send_confirmation_email_after_payment_timeout(submission.id)

        # assert that no e-mail was sent
        self.assertEqual(len(mail.outbox), 0)
