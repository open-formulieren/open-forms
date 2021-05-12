from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTests(TestCase):
    def test_validate_content_can_be_parsed(self):
        email = ConfirmationEmailTemplate(content="{{{}}}")

        with self.assertRaises(ValidationError):
            email.clean()

    @override_settings(EMAIL_TEMPLATE_URL_ALLOWLIST=["whitelisted.com"])
    def test_strip_non_whitelisted_urls(self):
        email = ConfirmationEmailTemplate(
            content="test https://google.com https://www.google.com https://whitelisted.com test"
        )

        rendered = email.render({})

        self.assertNotIn("google.com", rendered)
        self.assertIn("https://whitelisted.com", rendered)

    @override_settings(EMAIL_TEMPLATE_URL_ALLOWLIST=["whitelisted.com"])
    def test_strip_non_whitelisted_urls_from_context(self):
        email = ConfirmationEmailTemplate(content="test {{url1}} {{url2}} test")

        rendered = email.render(
            {"url1": "https://whitelisted.com", "url2": "https://google.com"}
        )

        self.assertNotIn("google.com", rendered)
        self.assertIn("https://whitelisted.com", rendered)
