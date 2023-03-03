import threading
import time
from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils.translation import gettext as _, override as override_language

from privates.test import temp_private_root

from openforms.appointments.constants import AppointmentDetailsStatus
from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.config.models import GlobalConfiguration
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.forms.constants import ConfirmationEmailOptions
from openforms.forms.tests.factories import FormStepFactory
from openforms.utils.tests.html_assert import HTMLAssertMixin

from ..tasks import maybe_send_confirmation_email
from ..tasks.emails import send_confirmation_email
from .factories import SubmissionFactory, SubmissionStepFactory


@temp_private_root()
class ConfirmationEmailTests(HTMLAssertMixin, TestCase):
    def test_task_without_mail_template(self):
        submission = SubmissionFactory.create()
        assert (
            not ConfirmationEmailTemplate.objects.exists()
        ), "There should not be any mail templates"

        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            maybe_send_confirmation_email(submission.id)

        self.assertEqual(len(mail.outbox), 0)

    def test_task_with_unexpected_failure(self):
        class CustomError(Exception):
            pass

        submission = SubmissionFactory.create()
        ConfirmationEmailTemplateFactory.create(form=submission.form)

        patcher = patch(
            "openforms.submissions.tasks.emails._send_confirmation_email",
            side_effect=CustomError("oops"),
        )
        with patcher, self.assertRaises(CustomError):
            send_confirmation_email(submission.id)

        self.assertEqual(len(mail.outbox), 0)

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
        form_step = FormStepFactory.create(
            form=submission.form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "foo",
                        "type": "textfield",
                        "label": "Foo",
                        "showInEmail": True,
                    }
                ],
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"foo": "bar"},
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )

        # "execute" the celery task
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            maybe_send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, "Confirmation mail")
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["test@test.nl"])

        self.assertIn("Information filled in: bar", message.body)
        self.assertNotIn("<table", message.body)

        # Check that the HTML template is used
        html_message, mime_type = message.alternatives[0]
        self.assertEqual(mime_type, "text/html")
        self.assertIn("<table", html_message)
        self.assertIn("Information filled in: bar", html_message)

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
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
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
                {
                    "key": "email",
                    "type": "email",
                    "confirmationRecipient": True,
                    "label": "Email",
                },
                {
                    "key": "foo",
                    "type": "textfield",
                    "showInEmail": True,
                    "label": "Foo",
                },
            ],
            submitted_data={"foo": "foovalue", "email": "test@test.nl"},
        )
        # add second step
        form_step = FormStepFactory.create(
            form_definition__configuration={
                "components": [
                    {
                        "key": "bar",
                        "type": "textfield",
                        "label": "Bar",
                        "showInEmail": True,
                    },
                    {
                        "key": "hello",
                        "type": "textfield",
                        "label": "Hello",
                        "showInEmail": False,
                    },
                ],
            },
            form=submission.form,
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"bar": "barvalue", "hello": "hellovalue"},
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation mail",
            content="Information filled in: {{ foo }} and {{ bar }}. Submission summary: {% summary %}",
        )

        # "execute" the celery task
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            maybe_send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn("Information filled in: foovalue and barvalue.", message.body)
        self.assertIn("Bar", message.body)
        self.assertIn("barvalue", message.body)
        self.assertIn("Foo", message.body)
        self.assertIn("foovalue", message.body)

        self.assertNotIn("Hello", message.body)
        self.assertNotIn("hellovalue", message.body)

        # Check that the HTML template is used
        html_message, mime_type = message.alternatives[0]
        self.assertEqual(mime_type, "text/html")
        self.assertIn("<table", html_message)
        self.assertIn("Information filled in: foovalue and barvalue.", html_message)
        self.assertTagWithTextIn("td", "Bar", html_message)
        self.assertTagWithTextIn("td", "barvalue", html_message)
        self.assertTagWithTextIn("td", "Foo", html_message)
        self.assertTagWithTextIn("td", "foovalue", html_message)

        self.assertNotTagWithTextIn("td", "Hello", html_message)
        self.assertNotTagWithTextIn("td", "hellovalue", html_message)

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
        form_step = FormStepFactory.create(
            form_definition__configuration={
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
            form=submission.form,
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"many": ["many1@test.nl", "many2@test.nl"]},
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )

        # "execute" the celery task
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
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

        with patch.object(send_confirmation_email, "apply_async") as mock_apply_async:
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

        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            # "execute" the celery task
            send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

    def test_completed_submission_sends_global_configuration_email_by_default(
        self,
    ):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_subject = "The Subject"
        config.confirmation_email_content = "The Content"
        config.save()

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

        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            # "execute" the celery task
            send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "The Subject")
        self.assertEqual(message.body.strip(), "The Content")

    def test_completed_submission_sends_global_configuration_email_when_custom_email_exists_but_is_not_selected(
        self,
    ):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_subject = "The Subject"
        config.confirmation_email_content = "The Content"
        config.save()

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
        ConfirmationEmailTemplateFactory.create(
            form=submission.form, subject="Custom subject", content="Custom content"
        )
        submission.form.confirmation_email_option = (
            ConfirmationEmailOptions.global_email
        )
        submission.form.save(update_fields=["confirmation_email_option"])

        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            # "execute" the celery task
            send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "The Subject")
        self.assertEqual(message.body.strip(), "The Content")

    def test_completed_submission_sends_form_specific_email_and_not_global_email(
        self,
    ):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_subject = "The Subject"
        config.confirmation_email_content = "The Content"
        config.save()

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
        ConfirmationEmailTemplateFactory.create(
            form=submission.form, subject="Custom subject", content="Custom content"
        )

        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            # "execute" the celery task
            send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Custom subject")
        self.assertEqual(message.body.strip(), "Custom content")

    def test_completed_submission_does_not_send_email_if_not_sending_email_is_specified(
        self,
    ):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_subject = "The Subject"
        config.confirmation_email_content = "The Content"
        config.save()

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
        ConfirmationEmailTemplateFactory.create(
            form=submission.form, subject="Custom subject", content="Custom content"
        )
        submission.form.confirmation_email_option = ConfirmationEmailOptions.no_email
        submission.form.save(update_fields=["confirmation_email_option"])

        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            # "execute" the celery task
            send_confirmation_email(submission.id)

        # Verify that email was not sent
        self.assertEqual(len(mail.outbox), 0)

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
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
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
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            send_confirmation_email(submission.id)

        # assert that no e-mail was sent
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    def test_send_confirmation_email_when_appointment_is_changed(self):
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
            has_previous_submission=True,
        )
        AppointmentInfoFactory.create(
            submission=submission.previous_submission,
            status=AppointmentDetailsStatus.cancelled,
        )
        # add a second step
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form=submission.form,
            data={"foo": "bar"},
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )

        # "execute" the celery task
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            maybe_send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, f"Confirmation mail {_('(updated)')}")

    def test_template_is_rendered_in_submission_language(self):
        """
        Assert a subset of the components with particularly weird APIs is translated correctly.

        Translations on all FormIO components are exercised (until exorcised) in
        ``DownloadSubmissionReportTests.test_report_is_generated_in_same_language_as_submission``
        (in the ``.test_submission_report`` module).
        """

        language = "en"
        with override_language(language):
            submission = SubmissionFactory.from_components(
                language_code=language,
                completed=True,
                components_list=[
                    {
                        "key": "email",
                        "type": "email",
                        "label": "Email",
                        "confirmationRecipient": True,
                    },
                ],
                submitted_data={
                    "email": "abuse@example.com",
                    "fubar": "Haveibeenpwned.com123!@#",
                    "editgrid1": [
                        {
                            "radio1": "radiov2",
                        },
                        {
                            "radio1": "radiov1",
                            "select1": "selectv2",
                        },
                    ],
                },
                form__generate_minimal_setup=True,
                form__translation_enabled=True,
                form__name="Translated form name",
                form__formstep__form_definition__name="A Quickstep",
                form__formstep__form_definition__component_translations={
                    "en": {
                        "Untranslated Repeating Group label": "Translated Repeating Group label",
                        "Untranslated Repeating Group Item label": "Translated Repeating Group Item label",
                        "Untranslated Radio option 1": "Translated Radio option 1",
                        "Untranslated Radio option 2": "Translated Radio option 2",
                        "Untranslated Select option 2": "Translated Select option 2",
                    },
                },
                form__formstep__form_definition__configuration={
                    "components": [
                        {
                            "key": "foo",
                            "type": "textfield",
                            "label": "Label with no translation",
                            "showInEmail": True,
                        },
                        {
                            "key": "fubar",
                            "type": "password",
                            "label": "Label with no translation",
                            # XXX cleartext "password" in email, for when you
                            # run out of room for Post-it™ on your monitor.
                            "showInEmail": True,
                        },
                        {
                            "type": "editgrid",
                            "key": "editgrid1",
                            "hidden": False,
                            "label": "Untranslated Repeating Group label",
                            "groupLabel": "Untranslated Repeating Group Item label",
                            "components": [
                                {
                                    "key": "radio1",
                                    "type": "radio",
                                    "showInEmail": True,
                                    "values": [
                                        {
                                            "label": "Untranslated Radio option 1",
                                            "value": "radiov1",
                                        },
                                        {
                                            "label": "Untranslated Radio option 2",
                                            "value": "radiov2",
                                        },
                                    ],
                                },
                                {
                                    "key": "select1",
                                    "type": "select",
                                    "showInEmail": True,
                                    "data": {
                                        "values": [
                                            {
                                                "label": "Untranslated Select option 1",
                                                "value": "selectv1",
                                            },
                                            {
                                                "label": "Untranslated Select option 2",
                                                "value": "selectv2",
                                            },
                                        ],
                                    },
                                },
                            ],
                        },
                    ],
                },
            )
            ConfirmationEmailTemplateFactory.create(
                form=submission.form,
                subject="Translated confirmation mail",
                content="""Translated content
                {{form_name}}
                {% summary %}
                """,
            )

        # "execute" the celery task
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            maybe_send_confirmation_email(submission.id)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, "Translated confirmation mail")
        self.assertEqual(message.to, ["abuse@example.com"])

        html_message, _ = message.alternatives[0]
        self.assertIn("Translated content", html_message)
        self.assertIn("Translated form name", html_message)
        self.assertIn("A Quickstep", html_message)

        self.assertNotIn("Untranslated", html_message)
        self.assertIn("Label with no translation", html_message)
        self.assertIn("Translated Repeating Group label", html_message)
        self.assertIn("Translated Repeating Group Item label 1", html_message)
        self.assertIn("Translated Radio option 2", html_message)
        self.assertIn("Translated Repeating Group Item label 2", html_message)
        self.assertIn("Translated Radio option 1", html_message)
        self.assertIn("Translated Select option 2", html_message)
        self.assertIn("************************", html_message)


class RaceConditionTests(TransactionTestCase):
    @patch("openforms.submissions.tasks.emails._send_confirmation_email")
    def test_concurrent_send_confirmation_email_calls(
        self, mock_send_confirmation_email
    ):
        """
        Assert that simultaneously scheduled send_email tasks do not run twice.

        There exists a race condition with the browser return flow + webhook return flow.
        """
        submission = SubmissionFactory.create(
            completed=True, confirmation_email_sent=False
        )
        ConfirmationEmailTemplateFactory.create(form=submission.form, content="test")

        def fake_send(*args, **kwargs):
            time.sleep(0.5)

        mock_send_confirmation_email.side_effect = fake_send

        def do_send_confirmation_email():
            send_confirmation_email(submission.id)
            close_old_connections()

        thread1 = threading.Thread(target=do_send_confirmation_email)
        thread2 = threading.Thread(target=do_send_confirmation_email)
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        mock_send_confirmation_email.assert_called_once()
