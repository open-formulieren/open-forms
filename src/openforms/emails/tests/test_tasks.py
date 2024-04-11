from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from django_yubin.models import Message
from freezegun import freeze_time

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory
from openforms.logging import logevent
from openforms.prefill.registry import register
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.tests.factories import SubmissionFactory
from stuf.stuf_bg.client import NoServiceConfigured

from ..tasks import send_email_digest


@override_settings(LANGUAGE_CODE="en")
class EmailDigestTaskTests(TestCase):
    def test_create_digest_email(self):
        submission = SubmissionFactory.create()

        with freeze_time("2023-01-02T12:30:00+01:00"):
            # Log email failed within last day
            logevent.email_status_change(
                submission,
                event="registration",
                status=Message.STATUS_FAILED,
                status_label="Failed",
                include_in_daily_digest=True,
            )

            # Successfully sent email
            logevent.email_status_change(
                submission,
                event="registration",
                status=Message.STATUS_SENT,
                status_label="Sent",
                include_in_daily_digest=True,
            )

        with freeze_time("2023-01-01T12:30:00+01:00"):
            # Log email failed more than 24h ago
            logevent.email_status_change(
                submission,
                event="registration",
                status=Message.STATUS_FAILED,
                status_label="Failed",
                include_in_daily_digest=True,
            )

        with (
            freeze_time("2023-01-03T01:00:00+01:00"),
            patch(
                "openforms.emails.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(
                    recipients_email_digest=["tralala@test.nl", "trblblb@test.nl"]
                ),
            ),
        ):
            send_email_digest()

        sent_email = mail.outbox[0]
        submission_occurences = sent_email.body.count(str(submission.uuid))

        self.assertEqual(
            sent_email.subject, "[Open Forms] Daily summary of detected problems"
        )
        self.assertEqual(
            sent_email.recipients(), ["tralala@test.nl", "trblblb@test.nl"]
        )
        self.assertEqual(submission_occurences, 1)

    def test_that_repeated_failures_are_not_mentioned_multiple_times(self):
        submission = SubmissionFactory.create()

        with freeze_time("2023-01-02T12:30:00+01:00"):
            logevent.email_status_change(
                submission,
                event="registration",
                status=Message.STATUS_FAILED,
                status_label="Failed",
                include_in_daily_digest=True,
            )
        with freeze_time("2023-01-02T13:30:00+01:00"):
            logevent.email_status_change(
                submission,
                event="registration",
                status=Message.STATUS_FAILED,
                status_label="Failed",
                include_in_daily_digest=True,
            )

        with (
            freeze_time("2023-01-03T01:00:00+01:00"),
            patch(
                "openforms.emails.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(
                    recipients_email_digest=["tralala@test.nl", "trblblb@test.nl"]
                ),
            ),
        ):
            send_email_digest()

        sent_email = mail.outbox[0]
        submission_occurencies = sent_email.body.count(str(submission.uuid))

        self.assertEqual(
            sent_email.subject, "[Open Forms] Daily summary of detected problems"
        )
        self.assertEqual(
            sent_email.recipients(), ["tralala@test.nl", "trblblb@test.nl"]
        )
        self.assertEqual(submission_occurencies, 1)

    def test_no_email_sent_if_no_logs(self):
        with patch(
            "openforms.emails.tasks.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                recipients_email_digest=["tralala@test.nl"]
            ),
        ):
            send_email_digest()

        self.assertEqual(0, len(mail.outbox))

    def test_no_email_sent_if_no_recipients(self):
        submission = SubmissionFactory.create()

        with freeze_time("2023-01-02T12:30:00+01:00"):
            logevent.email_status_change(
                submission,
                event="registration",
                status=Message.STATUS_FAILED,
                status_label="Failed",
                include_in_daily_digest=True,
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

    def test_email_sent_if_failed_submissions_exist(self):
        # 1st form with 2 failures in the past 24 hours
        form_1 = FormFactory.create()
        failed_submission_1 = SubmissionFactory.create(
            form=form_1, registration_status=RegistrationStatuses.failed
        )
        failed_submission_2 = SubmissionFactory.create(
            form=form_1, registration_status=RegistrationStatuses.failed
        )

        # 1st failure
        with freeze_time("2023-01-02T12:30:00+01:00"):
            logevent.registration_failure(
                failed_submission_1,
                RegistrationFailed("Registration plugin is not enabled"),
            )

        # 2nd failure
        with freeze_time("2023-01-02T18:30:00+01:00"):
            logevent.registration_failure(
                failed_submission_2,
                RegistrationFailed("Registration plugin is not enabled"),
            )

        # 2nd form with 1 failure in the past 24 hours
        form_2 = FormFactory.create()
        failed_submission = SubmissionFactory.create(
            form=form_2, registration_status=RegistrationStatuses.failed
        )

        # failure
        with freeze_time("2023-01-02T12:30:00+01:00"):
            logevent.registration_failure(
                failed_submission,
                RegistrationFailed("Registration plugin is not enabled"),
            )

        with (
            freeze_time("2023-01-03T01:00:00+01:00"),
            patch(
                "openforms.emails.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(
                    recipients_email_digest=["user@example.com"]
                ),
            ),
        ):
            send_email_digest()

        sent_email = mail.outbox[0]

        self.assertEqual(
            sent_email.subject, "[Open Forms] Daily summary of detected problems"
        )
        self.assertEqual(sent_email.recipients(), ["user@example.com"])
        self.assertIn(form_1.name, sent_email.body)
        self.assertIn(form_2.name, sent_email.body)

    def test_prefill_plugin_failures_are_sent(self):
        hc_plugin = register["haalcentraal"]
        stufbg_plugin = register["stufbg"]

        # 1st form with 2 failures in the past 24 hours
        form_1 = FormFactory.create()
        submission_1 = SubmissionFactory.create(form=form_1)
        submission_2 = SubmissionFactory.create(form=form_1)

        # 1st failure(no values)
        with freeze_time("2023-01-02T12:30:00+01:00"):
            logevent.prefill_retrieve_empty(
                submission_1, hc_plugin, ["burgerservicenummer"]
            )

        # 2nd failure(no values)
        with freeze_time("2023-01-02T18:30:00+01:00"):
            logevent.prefill_retrieve_empty(
                submission_2, hc_plugin, ["burgerservicenummer"]
            )

        # 2nd form with 1 failure in the past 24 hours
        form_2 = FormFactory.create()
        submission = SubmissionFactory.create(form=form_2)

        # failure(service not configured)
        with freeze_time("2023-01-02T12:30:00+01:00"):
            logevent.prefill_retrieve_failure(
                submission, stufbg_plugin, NoServiceConfigured()
            )

        with (
            freeze_time("2023-01-03T01:00:00+01:00"),
            patch(
                "openforms.emails.tasks.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(
                    recipients_email_digest=["user@example.com"]
                ),
            ),
        ):
            send_email_digest()

        sent_email = mail.outbox[0]

        self.assertEqual(
            sent_email.subject, "[Open Forms] Daily summary of detected problems"
        )
        self.assertEqual(sent_email.recipients(), ["user@example.com"])
        self.assertIn(form_1.name, sent_email.body)
        self.assertIn(form_2.name, sent_email.body)
        self.assertIn(str(submission_1.id), sent_email.body)
        self.assertIn(str(submission_2.id), sent_email.body)
        self.assertIn(str(submission.id), sent_email.body)
