from django.conf import settings
from django.core import mail
from django.core.exceptions import SuspiciousOperation
from django.template.loader import get_template
from django.test import TestCase

from pyquery import PyQuery

from openforms.config.models import GlobalConfiguration
from openforms.emails.context import _get_design_token_values
from openforms.emails.utils import send_mail_html


class HTMLEmailWrapperTest(TestCase):
    def test_send_mail_html(self):
        body = "<p>My Message</p>"
        attachments = [("file.bin", b"content", "application/foo")]
        send_mail_html(
            "My Subject",
            body,
            "foo@sender.com",
            ["foo@bar.baz"],
            attachment_tuples=attachments,
        )

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, "My Subject")
        self.assertEqual(message.recipients(), ["foo@bar.baz"])
        self.assertEqual(message.from_email, "foo@sender.com")

        # text
        self.assertEquals(message.body, "My Message\n")
        self.assertNotIn("<p>", message.body)

        # html alternative
        self.assertEqual(len(message.alternatives), 1)
        content, mime_type = message.alternatives[0]
        self.assertEquals(mime_type, "text/html")
        self.assertIn("<p>My Message</p>", content)
        self.assertIn("<table", content)

        # TODO test html validness?
        self.assertEqual(len(message.attachments), 1)
        file = message.attachments[0]
        self.assertEqual(file[0], "file.bin")
        self.assertEqual(file[1], b"content")  # still bytes
        self.assertEqual(file[2], "application/foo")

    def test_strip_non_allowed_urls(self):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["allowed.com"]
        config.save()

        body = "<p>test https://google.com https://www.google.com https://allowed.com test</p>"
        body += settings.BASE_URL

        send_mail_html(
            "My Subject",
            body,
            "foo@sender.com",
            ["foo@bar.baz"],
        )
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        message_html = message.alternatives[0][0]

        self.assertNotIn("google.com", message_html)
        self.assertIn("https://allowed.com", message_html)
        self.assertIn(settings.BASE_URL, message_html)

    def test_strip_non_allowed_urls_without_config_strips_all_urls_execpt_base_url(
        self,
    ):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = []
        config.save()

        body = "<p>test https://google.com https://www.google.com https://allowed.com test</p>"
        body += settings.BASE_URL
        send_mail_html(
            "My Subject",
            body,
            "foo@sender.com",
            ["foo@bar.baz"],
        )
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        message_html = message.alternatives[0][0]

        self.assertNotIn("google.com", message_html)
        self.assertNotIn("allowed.com", message_html)
        self.assertIn(settings.BASE_URL, message_html)

    def test_oversize_content_raise_suspiciosu_operation(self):
        body = "<p>My Message</p>" + ("123" * 1024 * 1024)
        with self.assertRaisesMessage(
            SuspiciousOperation, "email content-length exceeded safety limit"
        ):
            send_mail_html(
                "My Subject",
                body,
                "foo@sender.com",
                ["foo@bar.baz"],
            )


class DesignTokenFilterTest(TestCase):
    """unit tests for ``emails.context._get_design_token_values``"""

    def test_strip_px_unit(self):
        self.design_tokens = {
            "header-logo": {
                "height": {"value": "100px"},
                "width": {"value": "100px"},
            }
        }
        result = _get_design_token_values(self.design_tokens)
        self.assertEqual(result["logo"]["height"], "100px")
        self.assertEqual(result["logo"]["width"], "100px")
        self.assertEqual(result["logo"]["height_attr"], "100")
        self.assertEqual(result["logo"]["width_attr"], "100")

    def test_return_empty_string_for_non_px_unit(self):
        self.design_tokens = {
            "header-logo": {
                "height": {"value": "100em"},
                "width": {"value": "100em"},
            }
        }
        result = _get_design_token_values(self.design_tokens)
        self.assertEqual(result["logo"]["height"], "100em")
        self.assertEqual(result["logo"]["width"], "100em")
        self.assertEqual(result["logo"]["height_attr"], "")
        self.assertEqual(result["logo"]["width_attr"], "")

    def test_return_empty_string_for_auto_size(self):
        """default for width: 'auto'"""
        self.design_tokens = {"header-logo": {}}
        result = _get_design_token_values(self.design_tokens)
        self.assertEqual(result["logo"]["width"], "auto")
        self.assertEqual(result["logo"]["width_attr"], "")


class TemplateRenderingTest(TestCase):
    """
    integration test for the display of design token values

    assumes that ``emails.context.get_wrapper_context`` works correctly,
    hence the context variable is provided manually.
    """

    def test_design_token_values(self):
        template = get_template("emails/wrapper.html")
        ctx = {
            "content": "<p>Hello there!</p>",
            "main_website_url": "https://logoresizingdoneright.com",
            "style": {
                "logo": {
                    "height": "150px",
                    "width": "auto",
                    "height_attr": "150",
                    "width_attr": "",
                }
            },
            "logo_url": "https://logo.png",
        }
        html_message = template.render(ctx)
        img = PyQuery(html_message)("img")

        self.assertEqual(img.attr("height"), "150")
        self.assertIsNone(img.attr("width"))

        img_styles = img.attr("style").replace(" ", "").split(";")
        self.assertIn("width:auto", img_styles)
        self.assertIn("height:150px", img_styles)
