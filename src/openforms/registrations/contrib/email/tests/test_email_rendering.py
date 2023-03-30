from unittest.mock import patch

from django.test import TestCase

from openforms.config.models import GlobalConfiguration
from openforms.submissions.tests.factories import SubmissionFactory

from ..utils import get_registration_email_templates


class RenderRegistrationEmailTests(TestCase):
    def test_only_global_template_used(self):
        submission = SubmissionFactory.create(
            form__registration_email_subject="",
            form__registration_email_payment_subject="",
            form__registration_email_content_html="",
            form__registration_email_content_text="",
        )

        with patch(
            "openforms.registrations.contrib.email.utils.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                registration_email_subject="Global Subject",
                registration_email_payment_subject="Global Payment Subject",
                registration_email_content_html="Global HTML template",
                registration_email_content_text="Global text template",
            ),
        ):
            (
                subject_template,
                subject_payment_template,
                html_template,
                text_template,
            ) = get_registration_email_templates(submission)

        self.assertEqual(subject_template, "Global Subject")
        self.assertEqual(subject_payment_template, "Global Payment Subject")
        self.assertEqual(html_template, "Global HTML template")
        self.assertEqual(text_template, "Global text template")

    def test_can_overwrite_just_subject(self):
        submission = SubmissionFactory.create(
            form__registration_email_subject="Custom subject",
            form__registration_email_payment_subject="",
            form__registration_email_content_html="",
            form__registration_email_content_text="",
        )

        with patch(
            "openforms.registrations.contrib.email.utils.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                registration_email_subject="Global Subject",
                registration_email_payment_subject="Global Payment Subject",
                registration_email_content_html="Global HTML template",
                registration_email_content_text="Global text template",
            ),
        ):
            (
                subject_template,
                subject_payment_template,
                html_template,
                text_template,
            ) = get_registration_email_templates(submission)

        self.assertEqual(subject_template, "Custom subject")
        self.assertEqual(subject_payment_template, "Global Payment Subject")
        self.assertEqual(html_template, "Global HTML template")
        self.assertEqual(text_template, "Global text template")

    def test_can_overwrite_all_templates(self):
        submission = SubmissionFactory.create(
            form__registration_email_subject="Custom subject",
            form__registration_email_payment_subject="Custom Payment Subject",
            form__registration_email_content_html="Custom HTML template",
            form__registration_email_content_text="Custom text template",
        )

        with patch(
            "openforms.registrations.contrib.email.utils.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                registration_email_subject="Global Subject",
                registration_email_payment_subject="Global Payment Subject",
                registration_email_content_html="Global HTML template",
                registration_email_content_text="Global text template",
            ),
        ):
            (
                subject_template,
                subject_payment_template,
                html_template,
                text_template,
            ) = get_registration_email_templates(submission)

        self.assertEqual(subject_template, "Custom subject")
        self.assertEqual(subject_payment_template, "Custom Payment Subject")
        self.assertEqual(html_template, "Custom HTML template")
        self.assertEqual(text_template, "Custom text template")
