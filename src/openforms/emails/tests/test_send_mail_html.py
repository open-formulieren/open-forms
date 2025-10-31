from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.exceptions import SuspiciousOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.mail.backends.smtp import EmailBackend
from django.template.loader import get_template
from django.test import TestCase, override_settings

from django_yubin.models import Message
from pyquery import PyQuery

from openforms.config.models import GlobalConfiguration
from openforms.config.tests.factories import ThemeFactory
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import (
    X_OF_CONTENT_TYPE_HEADER,
    X_OF_CONTENT_UUID_HEADER,
    X_OF_EVENT_HEADER,
    EmailContentTypeChoices,
    EmailEventChoices,
)
from ..context import _get_design_token_values
from ..utils import send_mail_html


class HTMLEmailWrapperTest(TestCase):
    def setUp(self):
        super().setUp()

        self.addCleanup(GlobalConfiguration.clear_cache)

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
        assert isinstance(message, mail.EmailMultiAlternatives)
        self.assertEqual(message.subject, "My Subject")
        self.assertEqual(message.recipients(), ["foo@bar.baz"])
        self.assertEqual(message.from_email, "foo@sender.com")

        # text
        self.assertEqual(message.body, "My Message\n")
        assert isinstance(message.body, str)
        self.assertNotIn("<p>", message.body)

        # html alternative
        self.assertEqual(len(message.alternatives), 1)
        content, mime_type = message.alternatives[0]
        assert isinstance(content, str)
        self.assertEqual(mime_type, "text/html")
        self.assertIn("<p>My Message</p>", content)
        self.assertIn("<table", content)

        # TODO test html validity?
        self.assertEqual(len(message.attachments), 1)
        file = message.attachments[0]
        self.assertEqual(file[0], "file.bin")
        self.assertEqual(file[1], b"content")  # still bytes
        self.assertEqual(file[2], "application/foo")

    def test_strip_non_allowed_urls(self):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["allowed.com"]  # pyright: ignore[reportAttributeAccessIssue]
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
        assert isinstance(message, mail.EmailMultiAlternatives)
        message_html = message.alternatives[0][0]
        assert isinstance(message_html, str)

        self.assertNotIn("google.com", message_html)
        self.assertIn("https://allowed.com", message_html)
        self.assertIn(settings.BASE_URL, message_html)

    def test_strip_non_allowed_urls_without_config_strips_all_urls_execpt_base_url(
        self,
    ):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = []  # pyright: ignore[reportAttributeAccessIssue]
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
        assert isinstance(message, mail.EmailMultiAlternatives)
        message_html = message.alternatives[0][0]
        assert isinstance(message_html, str)

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

    def test_send_mail_html_when_theme_connected_to_form(self):
        theme_svg_content = b"""
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
        </svg>
        """

        theme = ThemeFactory.create(
            organization_name="The company",
            main_website="http://example.com",
            logo=SimpleUploadedFile(
                "theme-pixel.svg", theme_svg_content, content_type="image/svg+xml"
            ),
        )

        config = GlobalConfiguration.get_solo()
        config.organization_name = "Global company"
        config.main_website = "http://example-global.com"
        config.save()

        send_mail_html(
            subject="My Subject",
            html_body="<p>My Message</p>",
            from_email="foo@sender.com",
            recipient_list=["foo@bar.baz"],
            theme=theme,
        )

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        assert isinstance(message, mail.EmailMultiAlternatives)

        content, _ = message.alternatives[0]
        assert isinstance(content, str)

        # Theme's values should be rendered
        self.assertIn("http://example.com", content)
        self.assertIn("theme-pixel", content)
        self.assertNotIn("http://example-global.com", content)

    def test_send_mail_html_with_default_theme_configured(self):
        theme_svg_content = b"""
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
        </svg>
        """

        theme = ThemeFactory.create(
            organization_name="The company",
            main_website="http://example.com",
            logo=SimpleUploadedFile(
                "theme-pixel.svg", theme_svg_content, content_type="image/svg+xml"
            ),
        )

        config = GlobalConfiguration.get_solo()
        config.organization_name = "Global company"
        config.main_website = "http://example-global.com"
        config.default_theme = theme
        config.save()

        send_mail_html(
            subject="My Subject",
            html_body="<p>My Message</p>",
            from_email="foo@sender.com",
            recipient_list=["foo@bar.baz"],
        )

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        assert isinstance(message, mail.EmailMultiAlternatives)

        content, _ = message.alternatives[0]
        assert isinstance(content, str)

        # Theme's values should be rendered
        self.assertIn("http://example.com", content)
        self.assertIn("theme-pixel", content)
        self.assertNotIn("http://example-global.com", content)

    def test_send_mail_html_with_global_config_fallback(self):
        theme_svg_content = b"""
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
        </svg>
        """

        ThemeFactory.create(
            organization_name="The company",
            main_website="http://example.com",
            logo=SimpleUploadedFile(
                "theme-pixel.svg", theme_svg_content, content_type="image/svg+xml"
            ),
        )

        config = GlobalConfiguration.get_solo()
        config.organization_name = "Global company"
        config.main_website = "http://example-global.com"
        config.save()

        send_mail_html(
            subject="My Subject",
            html_body="<p>My Message</p>",
            from_email="foo@sender.com",
            recipient_list=["foo@bar.baz"],
        )

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        assert isinstance(message, mail.EmailMultiAlternatives)

        content, _ = message.alternatives[0]
        assert isinstance(content, str)

        # Theme's values should not be rendered
        self.assertNotIn("http://example.com", content)


@override_settings(
    EMAIL_BACKEND="django_yubin.backends.QueuedEmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
    LANGUAGE_CODE="en",
)
class HTMLEmailLoggingTest(TestCase):
    def test_logging_email_status(self):
        submission = SubmissionFactory.create()

        with (
            patch.object(
                EmailBackend, "send_messages", side_effect=Exception("Cant send email!")
            ),
            self.captureOnCommitCallbacks(execute=True),
        ):
            send_mail_html(
                "My Subject",
                "<p>My Message</p>",
                "foo@sender.com",
                ["foo@bar.baz"],
                extra_headers={
                    "Content-Language": "BLA",
                    X_OF_CONTENT_TYPE_HEADER: EmailContentTypeChoices.submission,
                    X_OF_CONTENT_UUID_HEADER: str(submission.uuid),
                    X_OF_EVENT_HEADER: EmailEventChoices.registration,
                },
            )

        logs = TimelineLogProxy.objects.filter(
            template="logging/events/email_status_change.txt"
        )

        self.assertEqual(logs[0].content_object, submission)
        self.assertEqual(
            logs[0].extra_data,
            {
                "event": EmailEventChoices.registration,
                "status": Message.STATUS_QUEUED,
                "status_label": "Queued",
                "log_event": "email_status_change",
                "include_in_daily_digest": True,
                "submission_lifecycle": True,
            },
        )
        self.assertEqual(
            logs[1].extra_data,
            {
                "event": EmailEventChoices.registration,
                "status": Message.STATUS_IN_PROCESS,
                "status_label": "In process",
                "log_event": "email_status_change",
                "include_in_daily_digest": True,
                "submission_lifecycle": True,
            },
        )
        self.assertEqual(
            logs[2].extra_data,
            {
                "event": EmailEventChoices.registration,
                "status": Message.STATUS_FAILED,
                "status_label": "Failed",
                "log_event": "email_status_change",
                "include_in_daily_digest": True,
                "submission_lifecycle": True,
            },
        )

    def test_no_extra_headers(self):
        with patch.object(
            EmailBackend, "send_messages", side_effect=Exception("Cant send email!")
        ):
            send_mail_html(
                "My Subject",
                "<p>My Message</p>",
                "foo@sender.com",
                ["foo@bar.baz"],
                extra_headers={
                    "Content-Language": "BLA",  # No extra headers
                },
            )

        logs = TimelineLogProxy.objects.filter(
            template="logging/events/email_status_change.txt"
        )

        self.assertEqual(0, logs.count())

    def test_submission_deleted_before_sending_email(self):
        with patch.object(
            EmailBackend, "send_messages", side_effect=Exception("Cant send email!")
        ):
            send_mail_html(
                "My Subject",
                "<p>My Message</p>",
                "foo@sender.com",
                ["foo@bar.baz"],
                extra_headers={
                    "Content-Language": "BLA",
                    X_OF_CONTENT_TYPE_HEADER: EmailContentTypeChoices.submission,
                    X_OF_CONTENT_UUID_HEADER: "159d0127-3384-4209-9dbd-c18d04188df6",
                    X_OF_EVENT_HEADER: EmailEventChoices.registration,
                },
            )

        logs = TimelineLogProxy.objects.filter(
            template="logging/events/email_status_change.txt"
        )

        self.assertEqual(0, logs.count())

    def test_other_content_than_submission(self):
        with patch.object(
            EmailBackend, "send_messages", side_effect=Exception("Cant send email!")
        ):
            send_mail_html(
                "My Subject",
                "<p>My Message</p>",
                "foo@sender.com",
                ["foo@bar.baz"],
                extra_headers={
                    "Content-Language": "BLA",
                    X_OF_CONTENT_TYPE_HEADER: "NOT SUBMISSION",
                },
            )

        logs = TimelineLogProxy.objects.filter(
            template="logging/events/email_status_change.txt"
        )

        self.assertEqual(0, logs.count())


class DesignTokenFilterTest(TestCase):
    """unit tests for ``emails.context._get_design_token_values``"""

    def test_strip_px_unit(self):
        self.design_tokens = {
            "of": {
                "header-logo": {
                    "height": {"value": "100px"},
                    "width": {"value": "100px"},
                }
            }
        }
        result = _get_design_token_values(self.design_tokens)
        self.assertEqual(result["logo"]["height"], "100px")
        self.assertEqual(result["logo"]["width"], "100px")
        self.assertEqual(result["logo"]["height_attr"], "100")
        self.assertEqual(result["logo"]["width_attr"], "100")

    def test_return_empty_string_for_non_px_unit(self):
        self.design_tokens = {
            "of": {
                "header-logo": {
                    "height": {"value": "100em"},
                    "width": {"value": "100em"},
                }
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

        style_attr = img.attr("style")
        assert isinstance(style_attr, str)
        img_styles = style_attr.replace(" ", "").split(";")
        self.assertIn("width:auto", img_styles)
        self.assertIn("height:150px", img_styles)
