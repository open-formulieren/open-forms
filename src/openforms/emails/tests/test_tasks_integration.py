from pathlib import Path
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse

from django_yubin.models import Message
from freezegun import freeze_time
from furl import furl
from simple_certmanager.test.factories import CertificateFactory
from zgw_consumers.test.factories import ServiceFactory

from openforms.config.models import GlobalConfiguration
from openforms.contrib.brk.models import BRKConfig
from openforms.forms.tests.factories import FormFactory
from openforms.logging import logevent
from openforms.prefill.registry import register
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models.submission import Submission
from openforms.submissions.tests.factories import SubmissionFactory

from ..tasks import send_email_digest

TEST_FILES = Path(__file__).parent / "data"


@patch(
    "openforms.emails.tasks.GlobalConfiguration.get_solo",
    return_value=GlobalConfiguration(
        recipients_email_digest=["tralala@test.nl", "trblblb@test.nl"]
    ),
)
@override_settings(LANGUAGE_CODE="en")
class EmailDigestTaskIntegrationTests(TestCase):

    def test_that_repeated_failures_are_not_mentioned_multiple_times(
        self, mock_global_config
    ):
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

        with freeze_time("2023-01-03T01:00:00+01:00"):
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

    def test_no_email_sent_if_no_logs(self, mock_global_config):
        send_email_digest()

        self.assertEqual(0, len(mail.outbox))

    def test_no_email_sent_if_no_recipients(self, mock_global_config):
        mock_global_config.return_value = GlobalConfiguration(
            recipients_email_digest=[]
        )
        submission = SubmissionFactory.create()

        with freeze_time("2023-01-02T12:30:00+01:00"):
            logevent.email_status_change(
                submission,
                event="registration",
                status=Message.STATUS_FAILED,
                status_label="Failed",
                include_in_daily_digest=True,
            )

        with freeze_time("2023-01-03T01:00:00+01:00"):
            send_email_digest()

        self.assertEqual(0, len(mail.outbox))

    @patch(
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=None),
    )
    @freeze_time("2023-01-03T01:00:00+01:00")
    def test_email_sent_when_there_are_failures(self, mock_global_config, brk_config):
        """Integration test for all the possible failures

        - failed emails
        - failed registrations
        - failed prefill_plugins
        - broken configurations
        - invalid certificates
        """
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "addressNl",
                        "type": "addressNL",
                        "label": "AddressNL",
                        "defaultValue": {
                            "postcode": "",
                            "houseLetter": "",
                            "houseNumber": "",
                            "houseNumberAddition": "",
                        },
                    }
                ],
            },
        )

        submission = SubmissionFactory.create(
            form=form, registration_status=RegistrationStatuses.failed
        )
        hc_plugin = register["haalcentraal"]

        # trigger failures
        with freeze_time("2023-01-02T12:30:00+01:00"):
            logevent.email_status_change(
                submission,
                event="registration",
                status=Message.STATUS_FAILED,
                status_label="Failed",
                include_in_daily_digest=True,
            )
            logevent.registration_failure(
                submission,
                RegistrationFailed("Registration plugin is not enabled"),
            )
            logevent.prefill_retrieve_empty(
                submission, hc_plugin, ["burgerservicenummer"]
            )

            with (
                open(TEST_FILES / "test2.certificate", "r") as client_certificate_f,
                open(TEST_FILES / "test.key", "r") as key_f,
            ):
                certificate = CertificateFactory.create(
                    label="Test certificate",
                    public_certificate=File(
                        client_certificate_f, name="test.certificate"
                    ),
                    private_key=File(key_f, name="test.key"),
                )
                ServiceFactory.create(client_certificate=certificate)

        # send the email digest
        send_email_digest()
        sent_email = mail.outbox[-1]

        # assertions
        with self.subTest("failed email"):
            self.assertIn(
                f'Email for the event "registration" for submission {submission.uuid}.',
                sent_email.body,
            )

        with self.subTest("failed registration"):
            admin_submissions_url = furl(
                reverse("admin:submissions_submission_changelist")
            )
            admin_submissions_url.args = {
                "form__id__exact": form.id,
                "needs_on_completion_retry__exact": 1,
                "registration_time": "24hAgo",
            }

            self.assertIn(
                f"Form '{form.admin_name}' failed 1 time(s) between 12:30 p.m. and 12:30 p.m..",
                sent_email.body,
            )
            self.assertIn(admin_submissions_url.url, sent_email.body)

        with self.subTest("failed prefill plugin"):
            content_type = ContentType.objects.get_for_model(Submission).id
            admin_logs_url = furl(reverse("admin:logging_timelinelogproxy_changelist"))
            admin_logs_url.args = {
                "content_type": content_type,
                "object_id__in": submission.id,
                "extra_data__log_event__in": "prefill_retrieve_empty,prefill_retrieve_failure",
            }

            self.assertIn(
                f"'{hc_plugin.verbose_name}' plugin has failed 1 time(s) between 12:30 p.m. and 12:30 p.m.",
                sent_email.body,
            )
            self.assertIn(admin_logs_url.url, sent_email.body)

        with self.subTest("broken configuration"):
            self.assertIn(
                "The configuration for 'BRK Client' is invalid (KVK endpoint is not configured).",
                sent_email.body,
            )

        with self.subTest("invalid certificates"):
            admin_certificate_url = furl(
                reverse(
                    "admin:simple_certmanager_certificate_change",
                    kwargs={"object_id": certificate.id},
                )
            )

            self.assertIn("Test certificate: has invalid keypair.", sent_email.body)
            self.assertIn(admin_certificate_url.url, sent_email.body)
