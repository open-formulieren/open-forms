from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from openforms.config.models import GlobalConfiguration
from openforms.logging.models import TimelineLogProxy

from ..tasks import on_cosign, send_email_cosigner
from .factories import SubmissionFactory


class OnCompletionTests(TestCase):
    def test_no_cosigner_component_in_form(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "notCosign",
                    "type": "textfield",
                    "label": "Some component",
                },
            ],
            submitted_data={"notCosign": "some data"},
        )

        with patch("openforms.submissions.tasks.co_sign.send_mail_html") as mock_email:
            send_email_cosigner(submission.id)

        mock_email.assert_not_called()

    def test_cosigner_component_in_form_empty(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                },
            ],
            submitted_data={"cosign": ""},
        )

        with patch("openforms.submissions.tasks.co_sign.send_mail_html") as mock_email:
            send_email_cosigner(submission.id)

        mock_email.assert_not_called()

    def test_sending_email_causes_error(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
        )

        with patch(
            "openforms.submissions.tasks.co_sign.send_mail_html",
            side_effect=Exception("I failed!"),
        ) as mock_email:
            with self.assertRaises(Exception, msg="I failed!"):
                send_email_cosigner(submission.id)

        mock_email.assert_called_once()
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/cosigner_email_queuing_failure.txt"
            ).count(),
            1,
        )

    def test_happy_flow(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
        )

        send_email_cosigner(submission.id)

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/cosigner_email_queuing_success.txt"
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.recipients(), ["test@test.nl"])

    def test_form_link_allowed_in_email(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
        )

        send_email_cosigner(submission.id)

        email = mail.outbox[0]
        form_link = submission.form.get_absolute_url()

        self.assertIn(form_link, email.body)

    def test_form_link_not_allowed_in_email(self):
        config = GlobalConfiguration.get_solo()
        config.show_form_link_in_cosign_email = False
        config.save()

        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
        )

        send_email_cosigner(submission.id)

        email = mail.outbox[0]
        form_link = submission.form.get_absolute_url()

        self.assertNotIn(form_link, email.body)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OnCosignTests(TestCase):
    def test_on_cosign_submission(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                },
                {
                    "key": "main",
                    "type": "email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"cosign": "cosign@test.nl", "main": "main@test.nl"},
            completed=True,
            cosign_complete=True,
        )

        on_cosign(submission.id)

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.recipients(), ["main@test.nl", "cosign@test.nl"])
        self.assertEqual(email.cc, ["cosign@test.nl"])
