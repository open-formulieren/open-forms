from django.core import mail
from django.test import TestCase

from openforms.emails.utils import send_mail_html


class HTMLEmailWrapperTest(TestCase):
    def test_send_mail_html(self):
        body = "<p>My Message</p>"
        attachments = [("file.bin", b"content", "application/foo")]
        send_mail_html(
            "My Subject",
            ["foo@bar.baz"],
            "foo@sender.com",
            body,
            attachment_tuples=attachments,
        )

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, "My Subject")
        self.assertEqual(message.recipients(), ["foo@bar.baz"])
        self.assertEqual(message.from_email, "foo@sender.com")

        # text
        self.assertEquals(message.body, "My Message")
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
