from django.conf import settings
from django.core import mail
from django.test import TestCase

from openforms.config.models import GlobalConfiguration
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
