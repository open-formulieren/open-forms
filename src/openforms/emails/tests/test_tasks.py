from datetime import datetime
from textwrap import dedent
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from django_yubin.models import Message
from freezegun import freeze_time

from openforms.config.models import GlobalConfiguration
from openforms.logging.tests.factories import TimelineLogProxyFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..tasks import send_email_digest


@override_settings(LANGUAGE_CODE="en")
class EmailDigestTaskTest(TestCase):
    def test_create_digest_email(self):
        submission = SubmissionFactory.create()

        with freeze_time("2023-01-02T12:30:00+01:00"):
            # Log email failed within last day
            TimelineLogProxyFactory.create(
                template="logging/events/email_status_change.txt",
                content_object=submission,
                extra_data={
                    "status": Message.STATUS_FAILED,
                    "event": "registration",
                    "include_in_daily_digest": True,
                },
            )
            # Successfully sent email
            TimelineLogProxyFactory.create(
                template="logging/events/email_status_change.txt",
                content_object=submission,
                extra_data={
                    "status": Message.STATUS_SENT,
                    "include_in_daily_digest": True,
                },
            )

        with freeze_time("2023-01-01T12:30:00+01:00"):
            # Log email failed more than 24h ago
            TimelineLogProxyFactory.create(
                template="logging/events/email_status_change.txt",
                content_object=submission,
                timestamp=datetime(2023, 1, 1, 12, 30),
                extra_data={
                    "status": Message.STATUS_FAILED,
                    "include_in_daily_digest": True,
                },
            )

        with (
            freeze_time("2023-01-03T01:00:00+01:00"),
            patch(
                "openforms.emails.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(
                    recipients_email_digest=["tralala@test.nl", "trblblb@test.nl"]
                ),
            ),
            patch("openforms.emails.tasks.send_mail_html") as patch_email,
        ):
            send_email_digest()

        patch_email.assert_called_once()

        args = patch_email.call_args.args

        expected_content = dedent(
            f"""
            <p>
                Here is a summary of the emails that failed to send yesterday:
            </p>
            <ul>
                <li>- Email for the event "registration" for submission {submission.uuid}.</li>

            </ul>
        """
        ).strip()

        self.assertEqual(args[3], ["tralala@test.nl", "trblblb@test.nl"])
        self.assertHTMLEqual(
            expected_content,
            args[1].strip(),
        )

    def test_that_repeated_failures_are_not_mentioned_multiple_times(self):
        submission = SubmissionFactory.create()

        with freeze_time("2023-01-02T12:30:00+01:00"):
            TimelineLogProxyFactory.create(
                template="logging/events/email_status_change.txt",
                content_object=submission,
                extra_data={
                    "status": Message.STATUS_FAILED,
                    "event": "registration",
                    "include_in_daily_digest": True,
                },
            )
        with freeze_time("2023-01-02T13:30:00+01:00"):
            TimelineLogProxyFactory.create(
                template="logging/events/email_status_change.txt",
                content_object=submission,
                extra_data={
                    "status": Message.STATUS_FAILED,
                    "event": "registration",
                    "include_in_daily_digest": True,
                },
            )

        with (
            freeze_time("2023-01-03T01:00:00+01:00"),
            patch(
                "openforms.emails.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(
                    recipients_email_digest=["tralala@test.nl", "trblblb@test.nl"]
                ),
            ),
            patch("openforms.emails.tasks.send_mail_html") as patch_email,
        ):
            send_email_digest()

        args = patch_email.call_args.args

        expected_content = dedent(
            f"""
            <p>
                Here is a summary of the emails that failed to send yesterday:
            </p>
            <ul>
                <li>- Email for the event "registration" for submission {submission.uuid}.</li>

            </ul>
        """
        ).strip()

        self.assertHTMLEqual(
            expected_content,
            args[1].strip(),
        )

    def test_no_email_send_if_no_logs(self):
        with patch(
            "openforms.emails.tasks.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                recipients_email_digest=["tralala@test.nl"]
            ),
        ):
            send_email_digest()

        self.assertEqual(0, len(mail.outbox))

    def test_no_recipients(self):
        submission = SubmissionFactory.create()

        with freeze_time("2023-01-02T12:30:00+01:00"):
            TimelineLogProxyFactory.create(
                template="logging/events/email_status_change.txt",
                content_object=submission,
                extra_data={
                    "status": Message.STATUS_FAILED,
                    "event": "registration",
                    "include_in_daily_digest": True,
                },
            )

        with (
            freeze_time("2023-01-03T01:00:00+01:00"),
            patch(
                "openforms.emails.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(recipients_email_digest=[]),
            ),
        ):
            send_email_digest()

        self.assertEqual(0, len(mail.outbox))
