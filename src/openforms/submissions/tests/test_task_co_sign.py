from unittest.mock import patch

from django.core import mail
from django.test import TestCase

from openforms.config.models import GlobalConfiguration
from openforms.logging.models import TimelineLogProxy

from ..tasks import send_email_cosigner
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

        with patch("openforms.submissions.utils.send_mail_html") as mock_email:
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

        with patch("openforms.submissions.utils.send_mail_html") as mock_email:
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
            "openforms.submissions.tasks.emails.send_mail_html",
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

    @patch("openforms.submissions.tasks.emails.GlobalConfiguration.get_solo")
    def test_form_link_allowed_in_email(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(
            show_form_link_in_cosign_email=True
        )
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            form_url="http://testserver/myform/",
        )

        send_email_cosigner(submission.id)

        email = mail.outbox[0]
        form_link = submission.form_url

        self.assertIn(form_link, email.body)

    @patch("openforms.submissions.tasks.emails.GlobalConfiguration.get_solo")
    def test_form_link_not_allowed_in_email(self, mock_get_solo):
        mock_get_solo.return_value = GlobalConfiguration(
            show_form_link_in_cosign_email=False
        )
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            form_url="http://testserver/myform/",
        )

        send_email_cosigner(submission.id)

        email = mail.outbox[0]
        form_link = submission.form_url

        self.assertNotIn(form_link, email.body)
