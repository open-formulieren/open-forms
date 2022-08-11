import uuid

from django.core import mail
from django.test import TestCase, override_settings

from privates.test import temp_private_root

from openforms.appointments.service import AppointmentRegistrationFailed
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
            completed=True,
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
