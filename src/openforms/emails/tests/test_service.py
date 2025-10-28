from django.test import TestCase, override_settings

from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import (
    X_OF_CONTENT_TYPE_HEADER,
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
    EmailContentTypeChoices,
    EmailEventChoices,
)
from ..service import get_last_confirmation_email
from ..utils import send_mail_html


@override_settings(
    EMAIL_BACKEND="django_yubin.backends.QueuedEmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
)
class GetLastConfirmationEmailTests(TestCase):
    @staticmethod
    def send_email(submission, content: str, email_event: EmailEventChoices) -> None:
        send_mail_html(
            "Email",
            content,
            "openforms@example.com",
            ["receipient@example.com"],
            extra_headers={
                "Content-Language": submission.language_code,
                X_OF_CONTENT_TYPE_HEADER: EmailContentTypeChoices.submission,
                X_OF_CONTENT_UUID_HEADER: str(submission.uuid),
                X_OF_EVENT_HEADER: email_event,
            },
        )

    def test_multiple_confirmation_emails(self):
        submission = SubmissionFactory.create()

        self.send_email(submission, "Email 1", EmailEventChoices.confirmation)
        self.send_email(submission, "Email 2", EmailEventChoices.confirmation)
        self.send_email(submission, "Email 3", EmailEventChoices.confirmation)

        last_email = get_last_confirmation_email(submission)
        assert last_email is not None
        content, _ = last_email

        self.assertIn("Email 3", content)

    def test_no_confirmation_emails_for_submission(self):
        submission = SubmissionFactory.create()

        self.send_email(submission, "Email 1", EmailEventChoices.cosign_request)
        self.send_email(submission, "Email 2", EmailEventChoices.registration)

        self.assertIsNone(get_last_confirmation_email(submission))

    def test_no_emails_at_all_for_submission(self):
        submission_1 = SubmissionFactory.create()
        submission_2 = SubmissionFactory.create()

        self.send_email(submission_1, "Email 1", EmailEventChoices.confirmation)

        self.assertIsNone(get_last_confirmation_email(submission_2))
