import uuid
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from privates.test import temp_private_root

from openforms.appointments.exceptions import AppointmentRegistrationFailed
from openforms.appointments.tests.utils import setup_jcc
from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.forms.tests.factories import FormDefinitionFactory

from ..models import SubmissionReport, TemporaryFileUpload
from ..tasks import on_completion
from .factories import SubmissionFactory, SubmissionFileAttachmentFactory


@temp_private_root()
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OnCompletionTests(TestCase):
    def test_submission_form_without_appointment(self):
        submission = SubmissionFactory.from_components(
            completed_not_preregistered=True,
            form__registration_backend="email",
            form__registration_backend_options={
                "to_emails": ["test@register.nl"],
            },
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
        ConfirmationEmailTemplateFactory.create(form=submission.form)
        SubmissionFileAttachmentFactory.create(
            submission_step=submission.submissionstep_set.first()
        )

        on_completion(submission.id)

        submission.refresh_from_db()
        for task_id in submission.on_completion_task_ids:
            with self.subTest(f"{task_id}"):
                try:
                    uuid.UUID(task_id)
                except ValueError:
                    self.fail("Invalid task ID returned")

        self.assertEqual(
            len(submission.on_completion_task_ids), 6
        )  # 6 tasks in the chain
        # registration result reference
        self.assertTrue(submission.public_registration_reference.startswith("OF-"))
        self.assertTrue(SubmissionReport.objects.filter(submission=submission).exists())
        self.assertFalse(TemporaryFileUpload.objects.exists())
        self.assertEqual(
            len(mail.outbox), 2
        )  # registration backend + confirmation email

    def test_submission_form_with_incomplete_appointment(self):
        setup_jcc()
        components = FormDefinitionFactory.build(is_appointment=True).configuration[
            "components"
        ]
        submission = SubmissionFactory.from_components(
            completed=True,
            form__registration_backend="",
            components_list=components,
            submitted_data={"product": {"identifier": "79", "name": "Paspoort"}},
        )

        with self.assertRaises(AppointmentRegistrationFailed):
            on_completion(submission.id)

    def test_cosign_required_but_not_completed_skips_registration(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
        )

        with patch(
            "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
        ) as mock_registration:
            on_completion(submission.id)

        mock_registration.assert_not_called()

    def test_cosign_not_required_and_not_filled_in_proceeds_with_registration(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": False},
                },
            ],
            submitted_data={"cosign": ""},
            completed=True,
            cosign_complete=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
        )

        with patch(
            "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
        ) as mock_registration:
            on_completion(submission.id)

        mock_registration.assert_called_once()

    def test_no_cosign_proceeds_with_registration(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "notCosign",
                    "type": "textfield",
                    "label": "Not a cosign component",
                },
            ],
            submitted_data={"notCosign": "Hello"},
            completed=True,
            cosign_complete=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
        )

        with patch(
            "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
        ) as mock_registration:
            on_completion(submission.id)

        mock_registration.assert_called_once()

    def test_cosign_not_required_but_filled_in_does_not_proceed_with_registration(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": False},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__registration_backend="email",
            form__registration_backend_options={"to_emails": ["test@registration.nl"]},
        )

        with patch(
            "openforms.registrations.contrib.email.plugin.EmailRegistration.register_submission"
        ) as mock_registration:
            on_completion(submission.id)

        mock_registration.assert_not_called()
