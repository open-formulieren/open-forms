from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings, tag
from django.utils.translation import gettext_lazy as _

from freezegun import freeze_time
from privates.test import temp_private_root

from openforms.authentication.service import AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.forms.constants import LogicActionTypes, PropertyTypes
from openforms.forms.tests.factories import FormLogicFactory
from openforms.logging.models import TimelineLogProxy
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.registrations.base import PreRegistrationResult
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.tests.utils import log_flaky

from ..constants import PostSubmissionEvents, RegistrationStatuses
from ..models import SubmissionReport
from ..tasks import on_post_submission_event
from .factories import SubmissionFactory


@temp_private_root()
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, LANGUAGE_CODE="en")
class TaskOrchestrationPostSubmissionEventTests(TestCase):
    def test_submission_completed_cosign_and_payment_not_needed(self):
        # The registration should happen since we are not waiting on payment/cosign
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                }
            ],
            form__name="Pretty Form",
            submitted_data={"email": "test@test.nl"},
            completed_not_preregistered=True,
            cosign_complete=False,
            confirmation_email_sent=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation of your {{ form_name }} submission",
            content="Custom content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.submissions.public_references.generate_unique_submission_reference",
                return_value="OF-TEST!",
            ),
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        self.assertEqual(submission.public_registration_reference, "OF-TEST!")
        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        mock_registration.assert_called()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox

        self.assertEqual(1, len(mails))  # Confirmation email (registration is mocked)
        self.assertEqual(
            mails[0].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[0].to, ["test@test.nl"])
        self.assertEqual(mails[0].cc, [])

        submission.refresh_from_db()

        self.assertTrue(submission.confirmation_email_sent)
        self.assertFalse(submission.cosign_request_email_sent)
        self.assertNotEqual(submission.auth_info.value, "111222333")

    def test_submission_completed_cosign_needed(self):
        # The registration should not happen since we are waiting on cosign
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"email": "test@test.nl", "cosign": "cosign@test.nl"},
            completed_not_preregistered=True,
            cosign_complete=False,
            cosign_request_email_sent=False,
            confirmation_email_sent=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation of your {{ form_name }} submission",
            cosign_content="Custom content {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.submissions.public_references.generate_unique_submission_reference",
                return_value="OF-TEST!",
            ),
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        self.assertEqual(submission.public_registration_reference, "OF-TEST!")
        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        mock_registration.assert_not_called()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox

        # FLAKINESS HERE happens something, try to figure out what's going wrong
        if not mails:
            log_flaky()

            # try to detect why no registration email was sent
            print(f"{submission.registration_status=}")
            print(f"{submission.payment_required=}")
            print(f"{submission.confirmation_email_sent=}")
            print(f"{submission.form.send_confirmation_email=}")
            # and print logevents
            logs = TimelineLogProxy.objects.for_object(submission)
            for log in logs:
                print(log.message().strip())

        self.assertEqual(2, len(mails))
        self.assertEqual(
            mails[0].subject,
            "Co-sign request for {form_name}".format(form_name="Pretty Form"),
        )
        self.assertEqual(mails[0].to, ["cosign@test.nl"])
        self.assertEqual(
            mails[1].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[1].to, ["test@test.nl"])
        self.assertEqual(mails[1].cc, [])

        cosign_info = "This form will not be processed until it has been co-signed. A co-sign request was sent to cosign@test.nl."

        self.assertIn(cosign_info, mails[1].body.strip("\n"))

        submission.refresh_from_db()

        self.assertTrue(submission.cosign_request_email_sent)
        self.assertTrue(submission.confirmation_email_sent)
        self.assertEqual(submission.auth_info.value, "111222333")

    def test_submission_completed_payment_needed(self):
        # The registration should happen (old payment flow!)
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
            completed_not_preregistered=True,
            cosign_complete=False,
            confirmation_email_sent=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            form__product__price=10,
            form__payment_backend="demo",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation of your {{ form_name }} submission",
            content="Custom content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.submissions.public_references.generate_unique_submission_reference",
                return_value="OF-TEST!",
            ),
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
            patch(
                "openforms.registrations.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(wait_for_payment_to_register=False),
            ),
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        # We then create the submission payment, as it requires a public reference
        SubmissionPaymentFactory.create(
            submission=submission, amount=10, status=PaymentStatus.started
        )

        self.assertEqual(submission.public_registration_reference, "OF-TEST!")
        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        mock_registration.assert_called()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox

        self.assertEqual(1, len(mails))
        self.assertEqual(
            mails[0].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[0].to, ["test@test.nl"])
        self.assertEqual(mails[0].cc, [])

        payment_info = (
            "Payment of EUR 10.00 is required. You can pay using the link below."
        )

        self.assertIn(payment_info, mails[0].body.strip("\n"))

        submission.refresh_from_db()

        self.assertTrue(submission.confirmation_email_sent)
        self.assertFalse(submission.cosign_request_email_sent)
        self.assertNotEqual(submission.auth_info.value, "111222333")

    def test_submission_completed_payment_and_cosign_needed(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"email": "test@test.nl", "cosign": "cosign@test.nl"},
            completed_not_preregistered=True,
            cosign_complete=False,
            cosign_request_email_sent=False,
            confirmation_email_sent=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__product__price=10,
            form__payment_backend="demo",
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation of your {{ form_name }} submission",
            cosign_content="Custom content {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.submissions.public_references.generate_unique_submission_reference",
                return_value="OF-TEST!",
            ),
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        # We then create the submission payment, as it requires a public reference
        SubmissionPaymentFactory.create(
            submission=submission, amount=10, status=PaymentStatus.started
        )

        self.assertEqual(submission.public_registration_reference, "OF-TEST!")
        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        mock_registration.assert_not_called()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox

        self.assertEqual(2, len(mails))
        self.assertEqual(
            mails[0].subject,
            _("Co-sign request for {form_name}").format(form_name="Pretty Form"),
        )
        self.assertEqual(mails[0].to, ["cosign@test.nl"])
        self.assertEqual(
            mails[1].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[1].to, ["test@test.nl"])
        self.assertEqual(mails[1].cc, [])

        cosign_info = "This form will not be processed until it has been co-signed. A co-sign request was sent to cosign@test.nl."
        payment_info = (
            "Payment of EUR 10.00 is required. You can pay using the link below."
        )

        self.assertIn(cosign_info, mails[1].body.strip("\n"))
        self.assertIn(payment_info, mails[1].body.strip("\n"))

        submission.refresh_from_db()

        self.assertTrue(submission.cosign_request_email_sent)
        self.assertTrue(submission.confirmation_email_sent)
        self.assertEqual(submission.auth_info.value, "111222333")

    def test_cosign_done_payment_not_needed(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"email": "test@test.nl", "cosign": "cosign@test.nl"},
            completed=True,
            cosign_request_email_sent=True,
            cosign_complete=True,
            confirmation_email_sent=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation of your {{ form_name }} submission",
            cosign_content="Custom content {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            with self.captureOnCommitCallbacks(execute=True):
                on_post_submission_event(
                    submission.id, PostSubmissionEvents.on_completion
                )

        submission.refresh_from_db()

        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        mock_registration.assert_called()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox

        self.assertEqual(1, len(mails))
        self.assertEqual(
            mails[0].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[0].to, ["test@test.nl"])
        self.assertEqual(mails[0].cc, ["cosign@test.nl"])

        cosign_info = "This email is a confirmation that this form has been co-signed by cosign@test.nl and can now be processed."

        self.assertIn(cosign_info, mails[0].body.strip("\n"))

        submission.refresh_from_db()

        self.assertTrue(submission.cosign_confirmation_email_sent)
        self.assertNotEqual(submission.auth_info.value, "111222333")

    def test_cosign_done_payment_needed_not_done(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"email": "test@test.nl", "cosign": "cosign@test.nl"},
            with_public_registration_reference=True,
            cosign_request_email_sent=True,
            cosign_complete=True,
            confirmation_email_sent=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            form__product__price=10,
            form__payment_backend="demo",
            language_code="en",
        )
        SubmissionPaymentFactory.create(
            submission=submission, amount=10, status=PaymentStatus.started
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation of your {{ form_name }} submission",
            cosign_content="Custom content {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
            patch(
                "openforms.registrations.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(wait_for_payment_to_register=False),
            ),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                on_post_submission_event(
                    submission.id, PostSubmissionEvents.on_completion
                )

        submission.refresh_from_db()

        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        mock_registration.assert_called()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox

        self.assertEqual(1, len(mails))
        self.assertEqual(
            mails[0].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[0].to, ["test@test.nl"])
        self.assertEqual(mails[0].cc, ["cosign@test.nl"])

        cosign_info = "This email is a confirmation that this form has been co-signed by cosign@test.nl and can now be processed."
        payment_info = (
            "Payment of EUR 10.00 is required. You can pay using the link below."
        )

        self.assertIn(cosign_info, mails[0].body.strip("\n"))
        self.assertIn(payment_info, mails[0].body.strip("\n"))

        submission.refresh_from_db()

        self.assertTrue(submission.cosign_confirmation_email_sent)
        self.assertFalse(submission.payment_complete_confirmation_email_sent)
        self.assertNotEqual(submission.auth_info.value, "111222333")

    def test_cosign_done_payment_done(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"email": "test@test.nl", "cosign": "cosign@test.nl"},
            with_public_registration_reference=True,
            cosign_request_email_sent=True,
            cosign_complete=True,
            confirmation_email_sent=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            form__product__price=10,
            form__payment_backend="demo",
            language_code="en",
        )
        SubmissionPaymentFactory.create(
            submission=submission, amount=10, status=PaymentStatus.registered
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation of your {{ form_name }} submission",
            cosign_content="Custom content {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            with self.captureOnCommitCallbacks(execute=True):
                on_post_submission_event(
                    submission.id, PostSubmissionEvents.on_completion
                )

        submission.refresh_from_db()

        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        mock_registration.assert_called()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox

        self.assertEqual(1, len(mails))
        self.assertEqual(
            mails[0].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[0].to, ["test@test.nl"])
        self.assertEqual(mails[0].cc, ["cosign@test.nl"])

        cosign_info = "This email is a confirmation that this form has been co-signed by cosign@test.nl and can now be processed."
        payment_info = (
            "Payment of EUR 10.00 is required. You can pay using the link below."
        )

        self.assertIn(cosign_info, mails[0].body.strip("\n"))
        self.assertNotIn(payment_info, mails[0].body.strip("\n"))

        submission.refresh_from_db()

        self.assertTrue(submission.cosign_confirmation_email_sent)
        self.assertTrue(submission.payment_complete_confirmation_email_sent)
        self.assertNotEqual(submission.auth_info.value, "111222333")

    def test_payment_done_cosign_not_needed(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
            with_public_registration_reference=True,
            confirmation_email_sent=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
            with_completed_payment=True,
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation of your {{ form_name }} submission",
            content="Custom content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
            patch(
                "openforms.registrations.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(wait_for_payment_to_register=False),
            ),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                on_post_submission_event(
                    submission.id, PostSubmissionEvents.on_completion
                )

        submission.refresh_from_db()

        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        mock_registration.assert_called()
        mock_payment_status_update.assert_called()

        mails = mail.outbox

        self.assertEqual(1, len(mails))
        self.assertEqual(
            mails[0].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[0].to, ["test@test.nl"])
        self.assertEqual(mails[0].cc, [])

        cosign_info = "This email is a confirmation that this form has been co-signed by cosign@test.nl and can now be processed."
        payment_info = (
            "Payment of EUR 10.00 is required. You can pay using the link below."
        )

        self.assertNotIn(cosign_info, mails[0].body.strip("\n"))
        self.assertNotIn(payment_info, mails[0].body.strip("\n"))

        submission.refresh_from_db()

        self.assertFalse(submission.cosign_confirmation_email_sent)
        self.assertTrue(submission.payment_complete_confirmation_email_sent)
        self.assertNotEqual(submission.auth_info.value, "111222333")

    def test_payment_done_cosign_needed_not_done(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"email": "test@test.nl", "cosign": "cosign@test.nl"},
            with_public_registration_reference=True,
            cosign_request_email_sent=True,
            cosign_complete=False,
            cosign_confirmation_email_sent=False,
            confirmation_email_sent=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
            with_completed_payment=True,
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation of your {{ form_name }} submission",
            cosign_content="Custom content {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            with self.captureOnCommitCallbacks(execute=True):
                on_post_submission_event(
                    submission.id, PostSubmissionEvents.on_completion
                )

        submission.refresh_from_db()

        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        mock_registration.assert_not_called()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox

        self.assertEqual(1, len(mails))
        self.assertEqual(
            mails[0].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[0].to, ["test@test.nl"])
        self.assertEqual(mails[0].cc, [])

        cosign_info = "This email is a confirmation that this form has been co-signed by cosign@test.nl and can now be processed."
        payment_info = (
            "Payment of EUR 10.00 is required. You can pay using the link below."
        )

        self.assertNotIn(cosign_info, mails[0].body.strip("\n"))
        self.assertNotIn(payment_info, mails[0].body.strip("\n"))

        submission.refresh_from_db()

        self.assertFalse(submission.cosign_confirmation_email_sent)
        self.assertTrue(submission.payment_complete_confirmation_email_sent)
        self.assertEqual(submission.auth_info.value, "111222333")

    def test_retry_flow(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"email": "test@test.nl", "cosign": "cosign@test.nl"},
            cosign_request_email_sent=True,
            cosign_complete=True,
            cosign_confirmation_email_sent=True,
            payment_complete_confirmation_email_sent=True,
            confirmation_email_sent=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            needs_on_completion_retry=True,
            registration_failed=True,
            with_public_registration_reference=True,
            with_completed_payment=True,
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            with self.captureOnCommitCallbacks(execute=True):
                on_post_submission_event(
                    submission.id, PostSubmissionEvents.on_completion
                )

        submission.refresh_from_db()

        mock_registration.assert_called()
        mock_payment_status_update.assert_called()

        mails = mail.outbox

        self.assertEqual(len(mails), 0)
        self.assertNotEqual(submission.auth_info.value, "111222333")

    def test_payment_status_update_retry_flow(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"email": "test@test.nl", "cosign": "cosign@test.nl"},
            registration_success=True,
            cosign_request_email_sent=True,
            cosign_complete=True,
            cosign_confirmation_email_sent=True,
            payment_complete_confirmation_email_sent=True,
            confirmation_email_sent=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            needs_on_completion_retry=True,
            with_completed_payment=True,
            with_public_registration_reference=True,
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            with self.captureOnCommitCallbacks(execute=True):
                on_post_submission_event(
                    submission.id, PostSubmissionEvents.on_completion
                )

        submission.refresh_from_db()

        mock_registration.assert_not_called()
        mock_payment_status_update.assert_called()

        mails = mail.outbox

        self.assertEqual(len(mails), 0)
        self.assertNotEqual(submission.auth_info.value, "111222333")

    def test_cosign_not_required_and_not_filled_in_proceeds_with_registration(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": False},
                },
            ],
            submitted_data={"cosign": "", "email": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            subject="Confirmation of your {{ form_name }} submission",
            content="Custom content {% appointment_information %} {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        mock_registration.assert_called_once()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox
        submission.refresh_from_db()

        # FLAKINESS HERE happens something, try to figure out what's going wrong
        if not mails:
            log_flaky()

            # try to detect why no registration email was sent
            print(f"{submission.registration_status=}")
            print(f"{submission.payment_required=}")
            print(f"{submission.confirmation_email_sent=}")
            print(f"{submission.form.send_confirmation_email=}")
            # and print logevents
            logs = TimelineLogProxy.objects.for_object(submission)
            for log in logs:
                print(log.message().strip())

        self.assertEqual(len(mails), 1)  # No cosign request email!

        self.assertEqual(
            mails[0].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[0].to, ["test@test.nl"])
        self.assertEqual(mails[0].cc, [])

        cosign_info = "This form will not be processed until it has been co-signed. A co-sign request was sent to cosign@test.nl."

        self.assertNotIn(cosign_info, mails[0].body.strip("\n"))

        self.assertFalse(submission.cosign_request_email_sent)
        self.assertTrue(submission.confirmation_email_sent)
        self.assertNotEqual(submission.auth_info.value, "111222333")

    def test_cosign_not_required_but_filled_in_does_not_proceed_with_registration(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": False},
                },
            ],
            submitted_data={"cosign": "cosign@test.nl", "email": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation of your {{ form_name }} submission",
            cosign_content="Custom content {% payment_information %} {% cosign_information %}",
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ) as mock_payment_status_update,
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        mock_registration.assert_not_called()
        mock_payment_status_update.assert_not_called()

        mails = mail.outbox

        self.assertEqual(2, len(mails))
        self.assertEqual(
            mails[0].subject,
            _("Co-sign request for {form_name}").format(form_name="Pretty Form"),
        )
        self.assertEqual(mails[0].to, ["cosign@test.nl"])
        self.assertEqual(
            mails[1].subject, "Confirmation of your Pretty Form submission"
        )
        self.assertEqual(mails[1].to, ["test@test.nl"])
        self.assertEqual(mails[1].cc, [])

        cosign_info = "This form will not be processed until it has been co-signed. A co-sign request was sent to cosign@test.nl."

        self.assertIn(cosign_info, mails[1].body.strip("\n"))

        submission.refresh_from_db()

        self.assertTrue(submission.cosign_request_email_sent)
        self.assertTrue(submission.confirmation_email_sent)
        self.assertEqual(submission.auth_info.value, "111222333")

    @tag("gh-3901", "hlmr-86")
    def test_cosign_required_but_hidden_proceeds_with_registration(self):
        """
        A conditionally hidden cosign component may not block registration.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "hidden": True,
                },
            ],
            submitted_data={"cosign": ""},
            completed=True,
            cosign_complete=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
        )
        assert submission.registration_status == RegistrationStatuses.pending

        on_post_submission_event(submission.pk, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        self.assertEqual(submission.registration_status, RegistrationStatuses.success)

    @tag("gh-3901", "hlmr-86")
    def test_cosign_required_and_visible_via_logic_does_not_proceed_with_registration(
        self,
    ):
        """
        A conditionally displayed cosign component must block registration.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "hidden": True,
                },
            ],
            submitted_data={"cosign": ""},
            completed=True,
            cosign_complete=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="111222333",
            language_code="en",
        )
        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.property,
                        "property": {
                            "type": PropertyTypes.bool,
                            "value": "hidden",
                        },
                        "state": False,
                    },
                    "component": "cosign",
                }
            ],
        )
        assert submission.registration_status == RegistrationStatuses.pending

        on_post_submission_event(submission.pk, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()
        self.assertEqual(submission.registration_status, RegistrationStatuses.pending)

    @tag("gh-3924")
    def test_payment_complete_does_not_set_retry_flag(self):
        submission = SubmissionFactory.create(
            form__payment_backend="demo",
            form__product__price=Decimal("11.35"),
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__name="Pretty Form",
            with_public_registration_reference=True,
            with_completed_payment=True,
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ),
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.update_payment_status"
            ),
            patch(
                "openforms.registrations.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(wait_for_payment_to_register=True),
            ),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                on_post_submission_event(
                    submission.id, PostSubmissionEvents.on_payment_complete
                )

            submission.refresh_from_db()

            self.assertFalse(submission.needs_on_completion_retry)

    @freeze_time("2024-02-16T18:15:00Z")
    def test_successful_registration_records_registration_counter_and_date(self):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed=True,
        )

        with (
            freeze_time("2024-02-16T21:15:00Z"),
            patch(
                "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.register_submission"
            ) as mock_registration,
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        mock_registration.assert_called()
        self.assertEqual(
            submission.last_register_date,
            datetime(2024, 2, 16, 21, 15).replace(tzinfo=UTC),
        )
        self.assertEqual(submission.registration_attempts, 1)

    @freeze_time("2024-02-16T18:15:00Z")
    def test_preregister_success_and_registration_failure_records_counter_and_date_only_once(
        self,
    ):
        zgw_group = ZGWApiGroupConfigFactory.create()
        submission = SubmissionFactory.create(
            form__registration_backend="zgw-create-zaak",
            form__registration_backend_options={
                "zgw_api_group": zgw_group.pk,
                "zaaktype": "https://catalogi.nl/api/v1/zaaktypen/1",
                "informatieobjecttype": "https://catalogi.nl/api/v1/informatieobjecttypen/1",
                "objects_api_group": None,
            },
            completed_not_preregistered=True,
        )

        with (
            freeze_time("2024-02-16T21:15:00Z"),
            patch(
                "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.contrib.zgw_apis.plugin.ZGWRegistration.pre_register_submission",
                return_value=PreRegistrationResult(
                    reference="ZAAK-ref", data={"zaak": {"some": "data"}}
                ),
            ) as mock_pre_registration,
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        submission.refresh_from_db()

        mock_pre_registration.assert_called()
        mock_registration.assert_called()
        self.assertTrue(submission.pre_registration_completed)
        self.assertEqual(
            submission.last_register_date,
            datetime(2024, 2, 16, 21, 15).replace(tzinfo=UTC),
        )
        self.assertEqual(submission.registration_attempts, 1)


@temp_private_root()
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class PaymentFlowTests(TestCase):
    def test_payment_required_and_not_should_wait_for_registration(self):
        """
        The payment is required and has not been completed, and the general configuration says to NOT skip registration if
        the payment has not been completed.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                }
            ],
            with_public_registration_reference=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__product__price=10,
            form__payment_backend="demo",
        )
        SubmissionPaymentFactory.create(
            submission=submission, amount=10, status=PaymentStatus.started
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(wait_for_payment_to_register=True),
            ),
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        mock_registration.assert_not_called()
        log_event = TimelineLogProxy.objects.for_object(submission).filter_event(
            "registration_skipped_not_yet_paid"
        )
        self.assertEqual(log_event.count(), 1)

    def test_payment_done_and_should_wait_for_payment(
        self,
    ):
        """
        The payment is required and has been completed, so registration should not be skipped regardless of the general
        configuration setting.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                }
            ],
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__product__price=10,
            form__payment_backend="demo",
            with_public_registration_reference=True,
            with_completed_payment=True,
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(wait_for_payment_to_register=True),
            ),
            patch(
                "openforms.payments.tasks.update_submission_payment_registration"
            ) as mock_update_payment_status,
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        mock_registration.assert_called_once()
        mock_update_payment_status.assert_not_called()

    def test_payment_done_and_not_should_wait_for_payment(
        self,
    ):
        """
        The payment is required and has been completed, so registration should not be skipped regardless of the general
        configuration setting.
        """

        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            form__product__price=10,
            form__payment_backend="demo",
            with_public_registration_reference=True,
            with_completed_payment=True,
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(wait_for_payment_to_register=False),
            ),
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        mock_registration.assert_called_once()

    def test_payment_not_required_and_should_wait_for_payment(
        self,
    ):
        """
        The payment is NOT required, so registration should not be skipped regardless of the general
        configuration setting.
        """
        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            completed=True,
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(wait_for_payment_to_register=True),
            ),
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        mock_registration.assert_called_once()

    def test_payment_not_required_and_not_should_wait_for_payment(
        self,
    ):
        """
        The payment is NOT required, so registration should not be skipped regardless of the general
        configuration setting.
        """
        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
            completed=True,
        )

        with (
            patch(
                "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
            ) as mock_registration,
            patch(
                "openforms.registrations.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(wait_for_payment_to_register=False),
            ),
        ):
            on_post_submission_event(submission.id, PostSubmissionEvents.on_completion)

        mock_registration.assert_called_once()
