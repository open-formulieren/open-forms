import base64
from email.mime.image import MIMEImage

from django.core import mail
from django.test import SimpleTestCase, TestCase

from openforms.utils.email import replace_datauri_images, send_mail_plus


class DataUriReplacement(SimpleTestCase):
    PNG_DATA = "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="

    def test_replacement_basic(self):
        datauri = f"data:image/png;base64,{self.PNG_DATA}"
        input_html = f'<body><img src="{datauri}" alt="my-image"></body>'

        html, images = replace_datauri_images(input_html)

        self.assertIsInstance(html, str)
        self.assertNotIn("data:image/", html)

        self.assertEqual(len(images), 1)

        img = images[0]
        self.assertEqual(img[0], "my-image-0")
        self.assertEqual(img[1], "image/png")
        self.assertIsInstance(img[2], bytes)
        self.assertEqual(img[2], base64.b64decode(self.PNG_DATA))

        self.assertIn(f' src="cid:{img[0]}"', html)

    def test_replacement_basic_no_alt(self):
        datauri = f"data:image/png;base64,{self.PNG_DATA}"
        input_html = f'<body><img src="{datauri}"></body>'

        html, images = replace_datauri_images(input_html)

        self.assertIsInstance(html, str)
        self.assertNotIn("data:image/", html)

        self.assertEqual(len(images), 1)

        img = images[0]
        self.assertEqual(img[0], "image-0")
        self.assertEqual(img[1], "image/png")
        self.assertIsInstance(img[2], bytes)
        self.assertEqual(img[2], base64.b64decode(self.PNG_DATA))

        self.assertIn(f' src="cid:{img[0]}"', html)

    def test__replacement_skips_unsuppored_mimetypes(self):
        datauri = f"data:text/plain;base64,{self.PNG_DATA}"
        input_html = f'<body><img src="{datauri}" alt="my-image"></body>'

        html, images = replace_datauri_images(input_html)

        self.assertIsInstance(html, str)
        self.assertIn(datauri, html)

        self.assertEqual(len(images), 0)

    def test_replacement_skips_regular_urls(self):
        uri = "http://example/image.jpg"
        input_html = f'<body><img src="{uri}" alt="my-image"></body>'

        html, images = replace_datauri_images(input_html)

        self.assertIsInstance(html, str)
        self.assertIn(uri, html)

        self.assertEqual(len(images), 0)


class SendMailPlusTest(TestCase):
    def test_send_mail_plus(self):
        data = "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
        datauri = f"data:image/png;base64,{data}"

        text_message = "My Message\n"
        html_message = f'<p>My Message <img src="{datauri}" alt="my-image"></p>'
        attachments = [("file.bin", b"content", "application/foo")]
        send_mail_plus(
            "My Subject",
            text_message,
            "foo@sender.com",
            ["foo@bar.baz"],
            html_message=html_message,
            attachments=attachments,
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
        self.assertIn("<p>My Message", content)

        # inline replaced datauri as img tag
        self.assertIn('<img src="cid:my-image-0" alt="my-image"/>', content)

        # same inline replaced datauri as attachment
        self.assertEqual(len(message.attachments), 2)
        file = message.attachments[0]
        self.assertIsInstance(file, MIMEImage)
        self.assertEqual(file["Content-Type"], "image/png")
        self.assertEqual(file["Content-ID"], "<my-image-0>")

        # regular attachment
        file = message.attachments[1]
        self.assertEqual(file[0], "file.bin")
        self.assertEqual(file[1], b"content")  # still bytes
        self.assertEqual(file[2], "application/foo")
