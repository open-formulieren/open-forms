from django.core import mail
from django.test import TestCase, tag

from ..tasks.emails import send_confirmation_email
from .factories import SubmissionFactory


class EmailSchedulingTests(TestCase):
    @tag("gh-4052")
    def test_emails_being_sent_multiple_times_on_payment(self):
        """
        An email was scheduled with timeout. But within that timeout the payment has happened and an email was sent
        immediately. When the task with timeout finally executes, it should see from the submission that the email has
        already been sent and not send again.
        """
        submission = SubmissionFactory.from_components(
            components_list=[
                {"key": "email", "type": "email", "confirmationRecipient": True},
            ],
            form__send_confirmation_email=True,
            completed=True,
            with_public_registration_reference=True,
            submitted_data={
                "email": "tralala@test.nl",
            },
            with_completed_payment=True,
            confirmation_email_sent=True,
            payment_complete_confirmation_email_sent=True,
        )

        send_confirmation_email(submission.pk)

        sent_mail = mail.outbox

        self.assertEqual(len(sent_mail), 0)
