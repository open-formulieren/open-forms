from django.core.exceptions import ValidationError
from django.test import TestCase

from openforms.config.models import GlobalConfiguration

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

        rendered = email.render({})

        self.assertNotIn("google.com", rendered)
        self.assertIn("https://allowed.com", rendered)

    def test_strip_non_allowed_urls_from_context(self):
        GlobalConfiguration.objects.create(
            email_template_netloc_allowlist=["allowed.com"]
        )

        email = ConfirmationEmailTemplate(content="test {{url1}} {{url2}} test")

        rendered = email.render(
            {"url1": "https://allowed.com", "url2": "https://google.com"}
        )

        self.assertNotIn("google.com", rendered)
        self.assertIn("https://allowed.com", rendered)

    def test_strip_non_allowed_urls_without_config_strips_all_urls(self):
        email = ConfirmationEmailTemplate(
            content="test https://google.com https://www.google.com https://allowed.com test"
        )

        rendered = email.render({})

        self.assertNotIn("google.com", rendered)
        self.assertNotIn("allowed.com", rendered)
