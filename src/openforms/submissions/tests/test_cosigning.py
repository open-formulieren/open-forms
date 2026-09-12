from django.core import mail
from django.test import TestCase

from openforms.config.tests.factories import ThemeFactory

from ..cosigning import send_cosign_otp
from .factories import SubmissionFactory


class SendCosignOTPTests(TestCase):
    def test_email_uses_form_theme(self):
        theme = ThemeFactory.create(
            design_token_values={"of": {"page-footer": {"bg": {"value": "#facade"}}}}
        )
        submission = SubmissionFactory.from_components(
            form__theme=theme,
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
        )

        send_cosign_otp(submission)

        self.assertEqual(len(mail.outbox), 1)
        html_content, _ = mail.outbox[0].alternatives[0]

        self.assertIn("#facade", html_content)
