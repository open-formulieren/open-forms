from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError
from django.test import TestCase

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTests(TestCase):
    def test_validate_content_can_be_parsed(self):
        email = ConfirmationEmailTemplate(content="{{{}}}")

        with self.assertRaises(ValidationError):
            email.clean()

    def test_strip_non_allowed_urls(self):
        GlobalConfiguration.objects.create(
            email_template_netloc_allowlist=["allowed.com"]
        )
        email = ConfirmationEmailTemplate(
            content="test https://google.com https://www.google.com https://allowed.com test"
        )

        rendered = email.render(SubmissionFactory.build())

        self.assertNotIn("google.com", rendered)
        self.assertIn("https://allowed.com", rendered)

    def test_strip_non_allowed_urls_from_context(self):
        form_step = FormStepFactory.create()
        subm_step = SubmissionStepFactory.create(
            data={"url1": "https://allowed.com", "url2": "https://google.com"},
            form_step=form_step,
            submission__form=form_step.form,
        )
        GlobalConfiguration.objects.create(
            email_template_netloc_allowlist=["allowed.com"]
        )

        email = ConfirmationEmailTemplate(content="test {{url1}} {{url2}} test")

        rendered = email.render(subm_step.submission)

        self.assertNotIn("google.com", rendered)
        self.assertIn("https://allowed.com", rendered)

    def test_strip_non_allowed_urls_without_config_strips_all_urls(self):
        email = ConfirmationEmailTemplate(
            content="test https://google.com https://www.google.com https://allowed.com test"
        )

        rendered = email.render(SubmissionFactory.build())

        self.assertNotIn("google.com", rendered)
        self.assertNotIn("allowed.com", rendered)

    def test_cant_delete_model_instances(self):
        form_step = FormStepFactory.create()
        subm_step = SubmissionStepFactory.create(
            data={"url1": "https://allowed.com", "url2": "https://google.com"},
            form_step=form_step,
            submission__form=form_step.form,
        )
        submission = subm_step.submission
        email = ConfirmationEmailTemplate(content="{{ _submission.delete }}")

        with self.assertRaises(ValidationError):
            email.full_clean()

        with self.assertRaises(TemplateSyntaxError):
            email.render(submission)

        submission.refresh_from_db()
        self.assertIsNotNone(submission.pk)
