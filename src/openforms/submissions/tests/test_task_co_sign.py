from unittest.mock import patch

from django.core import mail
from django.test import TestCase

from openforms.config.models import GlobalConfiguration
from openforms.emails.constants import EmailContentTypeChoices, EmailEventChoices
from openforms.logging.models import TimelineLogProxy

from ..tasks import send_email_cosigner
from .factories import SubmissionFactory

CO_SIGN_REQUEST_TEMPLATE = r"""
<p>
    This is a request to co-sign form "{{ form_name }}".
</p>

<p>
Please visit the form page by navigating to the following link: {{ form_url }}.
</p>

<p>
    You will then be redirected to authenticate yourself. After authentication, fill in
    the following code to retrieve the form submission:
    <br>
    <br>
    <strong>{{ code }}</strong>
</p>
"""


class OnCompletionTests(TestCase):

    def setUp(self):
        super().setUp()

        patcher = patch(
            "openforms.submissions.tasks.emails.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                cosign_request_template=CO_SIGN_REQUEST_TEMPLATE
            ),
        )
        self.m_get_solo = patcher.start()
        self.addCleanup(patcher.stop)

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
            form_url="http://testserver/myform/",
        )

        send_email_cosigner(submission.id)

        email = mail.outbox[0]
        form_link = submission.form_url

        self.assertIn(form_link, email.body)

    def test_form_link_not_allowed_in_email(self):
        self.m_get_solo.return_value.cosign_request_template = r"""
            {{ form_name }}
            <br>
            {{ code }}
        """

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
        self.assertIn(submission.public_registration_reference, email.body)

    def test_headers_in_cosign_request_email(self):
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

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]

        # UUID is not a constant, so just test if it exists
        submission_uuid = message.extra_headers.pop("X-OF-Content-UUID", None)
        self.assertIsNotNone(submission_uuid)

        # Test remaining headers
        self.assertEqual(
            message.extra_headers,
            {
                "Content-Language": "nl",
                "X-OF-Content-Type": EmailContentTypeChoices.submission,
                "X-OF-Event": EmailEventChoices.cosign_request,
            },
        )
