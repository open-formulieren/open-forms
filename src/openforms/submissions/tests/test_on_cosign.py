from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.registrations.contrib.email.models import EmailConfig

from ..constants import PostSubmissionEvents, RegistrationStatuses
from ..tasks import on_post_submission_event
from .factories import SubmissionFactory


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OnCosignTests(TestCase):
    def test_submission_on_cosign(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {"key": "cosignerEmail", "type": "cosign"},
                {"key": "mainEmail", "type": "email", "confirmationRecipient": True},
            ],
            co_sign_data={
                "plugin": "digid",
                "attribute": "bsn",
                "value": "123456782",
            },
            form__send_confirmation_email=True,
            completed=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["registration@test.nl"]},
            submitted_data={
                "mainEmail": "main@test.nl",
                "cosignerEmail": "cosigner@test.nl",
            },
            cosign_complete=True,
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation email whoop whoop",
        )

        with patch(
            "openforms.registrations.contrib.email.utils.EmailConfig.get_solo",
            return_value=EmailConfig(
                subject="Registration email whoop whoop",
            ),
        ):
            on_post_submission_event(
                submission.id, PostSubmissionEvents.on_cosign_complete
            )

        self.assertEqual(len(mail.outbox), 2)

        registration_email = mail.outbox[0]
        confirmation_email = mail.outbox[1]

        self.assertEqual(registration_email.subject, "Registration email whoop whoop")
        self.assertEqual(confirmation_email.subject, "Confirmation email whoop whoop")

    def test_registration_failure_does_not_abort_the_chain(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {"key": "cosignerEmail", "type": "cosign", "authPlugin": "digid"},
                {"key": "mainEmail", "type": "email", "confirmationRecipient": True},
            ],
            co_sign_data={
                "plugin": "digid",
                "attribute": "bsn",
                "value": "123456782",
            },
            form__send_confirmation_email=True,
            completed=True,
            cosign_complete=True,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["registration@test.nl"]},
            submitted_data={
                "mainEmail": "main@test.nl",
                "cosignerEmail": "cosigner@test.nl",
            },
        )
        ConfirmationEmailTemplateFactory.create(
            form=submission.form,
            cosign_subject="Confirmation email whoop whoop",
        )

        with patch(
            "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission",
            side_effect=Exception,
        ):
            on_post_submission_event(
                submission.id, PostSubmissionEvents.on_cosign_complete
            )

        self.assertEqual(len(mail.outbox), 1)

        confirmation_email = mail.outbox[0]

        self.assertEqual(confirmation_email.subject, "Confirmation email whoop whoop")

        submission.refresh_from_db()

        self.assertEqual(submission.registration_status, RegistrationStatuses.failed)
