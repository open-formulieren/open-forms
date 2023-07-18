from unittest.mock import patch

from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ..models import EmailConfig
from ..utils import get_registration_email_templates


class RenderRegistrationEmailTests(TestCase):
    def test_only_global_template_used(self):
        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={
                "to_emails": ["test@test.nl"],
            },
        )

        with patch(
            "openforms.registrations.contrib.email.utils.EmailConfig.get_solo",
            return_value=EmailConfig(
                subject="Global Subject",
                payment_subject="Global Payment Subject",
                content_html="Global HTML template",
                content_text="Global text template",
            ),
        ):
            templates = get_registration_email_templates(submission)

        self.assertEqual(templates.subject, "Global Subject")
        self.assertEqual(templates.payment_subject, "Global Payment Subject")
        self.assertEqual(templates.content_html, "Global HTML template")
        self.assertEqual(templates.content_text, "Global text template")

    def test_can_overwrite_just_subject(self):
        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={
                "to_emails": ["test@test.nl"],
                "email_subject": "Custom subject",
            },
        )

        with patch(
            "openforms.registrations.contrib.email.utils.EmailConfig.get_solo",
            return_value=EmailConfig(
                subject="Global Subject",
                payment_subject="Global Payment Subject",
                content_html="Global HTML template",
                content_text="Global text template",
            ),
        ):
            templates = get_registration_email_templates(submission)

        self.assertEqual(templates.subject, "Custom subject")
        self.assertEqual(templates.payment_subject, "Global Payment Subject")
        self.assertEqual(templates.content_html, "Global HTML template")
        self.assertEqual(templates.content_text, "Global text template")

    def test_can_overwrite_all_templates(self):
        submission = SubmissionFactory.create(
            form__registration_backend="email",
            form__registration_backend_options={
                "to_emails": ["test@test.nl"],
                "email_subject": "Custom subject",
                "email_payment_subject": "Custom Payment Subject",
                "email_content_template_html": "Custom HTML template",
                "email_content_template_text": "Custom text template",
            },
        )

        with patch(
            "openforms.registrations.contrib.email.utils.EmailConfig.get_solo",
            return_value=EmailConfig(
                subject="Global Subject",
                payment_subject="Global Payment Subject",
                content_html="Global HTML template",
                content_text="Global text template",
            ),
        ):
            templates = get_registration_email_templates(submission)

        self.assertEqual(templates.subject, "Custom subject")
        self.assertEqual(templates.payment_subject, "Custom Payment Subject")
        self.assertEqual(templates.content_html, "Custom HTML template")
        self.assertEqual(templates.content_text, "Custom text template")
