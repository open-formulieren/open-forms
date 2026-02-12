from pathlib import Path
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from django_yubin.models import Message
from freezegun import freeze_time
from furl import furl
from requests import RequestException
from simple_certmanager.test.factories import CertificateFactory
from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.config.models import GlobalConfiguration
from openforms.contrib.brk.models import BRKConfig
from openforms.contrib.brk.tests.base import INVALID_BRK_SERVICE
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
)
from openforms.logging import audit_logger
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.prefill.registry import register as prefill_register
from openforms.registrations.base import BasePlugin
from openforms.registrations.exceptions import RegistrationFailed
from openforms.registrations.registry import register as register_register
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.models.submission import Submission
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..tasks import send_email_digest

TEST_FILES = Path(__file__).parent / "data"


@register_register("integration-test-invalid-backend")
class InvalidBackend(BasePlugin):
    verbose_name = "Invalid backend"

    def register_submission(self, submission, options):
        pass

    def check_config(self):
        raise InvalidPluginConfiguration("Invalid")


@override_settings(LANGUAGE_CODE="en")
class EmailDigestTaskIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = GlobalConfiguration.get_solo()
        config.recipients_email_digest = ["tralala@test.nl", "trblblb@test.nl"]  # pyright: ignore[reportAttributeAccessIssue]
        config.save()

    def setUp(self):
        super().setUp()

        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_that_repeated_failures_are_not_mentioned_multiple_times(self):
        submission = SubmissionFactory.create()
        audit_log = audit_logger.bind(
            submission_uuid=str(submission.uuid),
            email_event="registration",
        )

        with freeze_time("2023-01-02T12:30:00+01:00"):
            audit_log.info(
                "email_status_change",
                new_status=Message.STATUS_FAILED,
                status_label="Failed",
            )
        with freeze_time("2023-01-02T13:30:00+01:00"):
            audit_log.info(
                "email_status_change",
                new_status=Message.STATUS_FAILED,
                status_label="Failed",
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

    def test_no_email_sent_if_no_logs(self):
        send_email_digest()

        self.assertEqual(0, len(mail.outbox))

    def test_no_email_sent_if_no_recipients(self):
        config = GlobalConfiguration.get_solo()
        config.recipients_email_digest = []  # pyright: ignore[reportAttributeAccessIssue]
        config.save()
        submission = SubmissionFactory.create()

        with freeze_time("2023-01-02T12:30:00+01:00"):
            audit_logger.info(
                "email_status_change",
                submission_uuid=str(submission.uuid),
                email_event="registration",
                new_status=Message.STATUS_FAILED,
                status_label="Failed",
            )

        with freeze_time("2023-01-03T01:00:00+01:00"):
            send_email_digest()

        self.assertEqual(0, len(mail.outbox))

    @patch(
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=INVALID_BRK_SERVICE),
    )
    @freeze_time("2023-01-03T01:00:00+01:00")
    @override_settings(BASE_URL="http://testserver")
    @requests_mock.Mocker()
    def test_email_sent_when_there_are_failures(self, brk_config, m):
        """Integration test for all the possible failures

        - failed emails
        - failed registrations
        - failed prefill_plugins
        - broken configurations
        - invalid certificates
        - invalid registration backends
        - invalid logic rules
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
                        "validate": {"plugins": ["brk-zakelijk-gerechtigd"]},
                    }
                ],
            },
        )

        submission = SubmissionFactory.create(
            form=form, registration_status=RegistrationStatuses.failed
        )
        hc_plugin = prefill_register["haalcentraal"]

        audit_log = audit_logger.bind(submission_uuid=str(submission.uuid))

        # trigger failures
        with freeze_time("2023-01-02T12:30:00+01:00"):
            audit_log.info(
                "email_status_change",
                email_event="registration",
                new_status=Message.STATUS_FAILED,
                status_label="Failed",
            )
            audit_log.warning(
                "registration_failure",
                plugin=register_register["integration-test-invalid-backend"],
                exc_info=RegistrationFailed("Registration plugin is not enabled"),
            )
            audit_log.info(
                "prefill_retrieve_empty",
                plugin=hc_plugin,
                attributes=["burgerservicenummer"],
            )
            FormRegistrationBackendFactory.create(
                form=form,
                key="plugin1",
                backend="integration-test-invalid-backend",
            )
            FormLogicFactory.create(
                form=form,
                json_logic_trigger={"==": [{"var": "foo"}, "apple"]},
            )
            FormLogicFactory.create(
                form=form,
                json_logic_trigger={"custom_operator": [5, 3]},
            )

            with (
                open(TEST_FILES / "test2.certificate") as client_certificate_f,
                open(TEST_FILES / "test.key") as key_f,
            ):
                certificate = CertificateFactory.create(
                    label="",
                    public_certificate=File(
                        client_certificate_f, name="test.certificate"
                    ),
                    private_key=File(key_f, name="test.key"),
                )
                ServiceFactory.create(client_certificate=certificate)

            m.get(
                "https://api.brk.kadaster.nl/invalid/kadastraalonroerendezaken?postcode=1234AB&huisnummer=1",
                status_code=400,
            )

        # send the email digest
        send_email_digest()
        sent_email = mail.outbox[-1]
        assert isinstance(sent_email.body, str)

        # assertions
        with self.subTest("failed email"):
            self.assertIn(
                f'Email for the event "registration" for submission {submission.uuid}.',
                sent_email.body,
            )

        with self.subTest("failed registration"):
            admin_relative_submissions_url = furl(
                reverse("admin:submissions_submission_changelist")
            )
            admin_relative_submissions_url.args.update(
                {
                    "form__id__exact": form.id,
                    "needs_on_completion_retry__exact": 1,
                    "registration_time": "24hAgo",
                }
            )
            admin_submissions_url = furl(
                f"http://testserver{admin_relative_submissions_url.url}"
            ).url

            self.assertIn(
                f"Form '{form.admin_name}' failed 1 time(s) between 12:30 p.m. and 12:30 p.m..",
                sent_email.body,
            )
            self.assertIn(admin_submissions_url, sent_email.body)

        with self.subTest("failed prefill plugin"):
            content_type = ContentType.objects.get_for_model(Submission).id
            admin_relative_logs_url = furl(
                reverse("admin:logging_timelinelogproxy_changelist")
            )
            admin_relative_logs_url.args.update(
                {
                    "content_type": content_type,
                    "object_id__in": submission.id,
                    "extra_data__log_event__in": "prefill_retrieve_empty,prefill_retrieve_failure",
                }
            )
            admin_logs_url = furl(f"http://testserver{admin_relative_logs_url.url}").url

            self.assertIn(
                f"'{hc_plugin.verbose_name}' plugin has failed 1 time(s) between 12:30 p.m. and 12:30 p.m.",
                sent_email.body,
            )
            self.assertIn(admin_logs_url, sent_email.body)

        with self.subTest("broken configuration"):
            self.assertIn(
                "The configuration for 'BRK Client' is invalid",
                sent_email.body,
            )

        with self.subTest("invalid certificates"):
            admin_relative_certificate_url = reverse(
                "admin:simple_certmanager_certificate_change",
                kwargs={"object_id": certificate.id},
            )
            admin_certificate_url = f"http://testserver{admin_relative_certificate_url}"

            self.assertIn("(missing label): has invalid keypair.", sent_email.body)
            self.assertIn(admin_certificate_url, sent_email.body)

        with self.subTest("invalid registration backends"):
            admin_relative_form_url = reverse(
                "admin:forms_form_change", kwargs={"object_id": form.id}
            )
            admin_form_url = f"http://testserver{admin_relative_form_url}"

            self.assertIn(
                f"The configuration for plugin '{InvalidBackend.verbose_name}' is invalid.",
                sent_email.body,
            )
            self.assertIn(admin_form_url, sent_email.body)

        with self.subTest("invalid logic rules"):
            self.assertIn(
                f"We couldn't process logic rule 2 for '{form.admin_name}' because it appears to be invalid.",
                sent_email.body,
            )
            self.assertIn(
                f"Logic rule for variable 'foo' is invalid in form '{form.admin_name}'.",
                sent_email.body,
            )


@override_settings(LANGUAGE_CODE="en")
class ReferenceListsExpiredDataTests(OFVCRMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        config = GlobalConfiguration.get_solo()
        config.recipients_email_digest = ["tralala@test.nl", "trblblb@test.nl"]  # pyright: ignore[reportAttributeAccessIssue]
        config.save()

        # The service is relative to the docker compose instance that we have in the
        # docker directory (docker-compose.referentielijsten.yml)
        cls.reference_lists_service = ServiceFactory.create(
            api_root="http://localhost:8004/api/v1/",
            slug="reference-lists",
            auth_type=AuthTypes.no_auth,
        )
        config.reference_lists_services.add(cls.reference_lists_service)

    def setUp(self) -> None:
        super().setUp()

        self.addCleanup(GlobalConfiguration.clear_cache)

    def test_tables(self):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "label": "Selectboxes",
                        "openForms": {
                            "dataSrc": "referenceLists",
                            "service": "reference-lists",
                            "code": "not-geldig-anymore	",
                        },
                    }
                ],
            },
        )

        # expiring
        with freeze_time("2020-01-30T12:30:00+01:00"):
            send_email_digest()
            sent_email = mail.outbox[-1]
            assert isinstance(sent_email.body, str)

            self.assertIn(
                "Table 'Tabel that is not geldig anymore' will expire in 3 days, 21 hours.",
                sent_email.body,
            )

        # expired
        with freeze_time("2020-03-30T12:30:00+01:00"):
            send_email_digest()
            sent_email = mail.outbox[-1]
            assert isinstance(sent_email.body, str)

            self.assertIn(
                "Table 'Tabel that is not geldig anymore' expired 1 month, 3 weeks ago.",
                sent_email.body,
            )

    def test_items(self):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "label": "Selectboxes",
                        "openForms": {
                            "dataSrc": "referenceLists",
                            "service": "reference-lists",
                            "code": "item-not-geldig-anymore",
                        },
                    }
                ],
            },
        )

        # expiring
        with freeze_time("2025-02-01T12:30:00+01:00"):
            send_email_digest()
            sent_email = mail.outbox[-1]
            assert isinstance(sent_email.body, str)

            self.assertIn(
                "Item 'Not geldig option' will expire in 6 days, 2 hours.",
                sent_email.body,
            )

        # expired
        with freeze_time("2025-03-01T12:30:00+01:00"):
            send_email_digest()
            sent_email = mail.outbox[-1]
            assert isinstance(sent_email.body, str)

            self.assertIn(
                "Item 'Not geldig option' expired 3 weeks ago.",
                sent_email.body,
            )

    @requests_mock.Mocker()
    def test_exception_for_tables_returns_proper_message(self, m):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "label": "Selectboxes",
                        "openForms": {
                            "dataSrc": "referenceLists",
                            "service": "reference-lists",
                            "code": "broken-table",
                        },
                    }
                ],
            },
        )

        m.get(
            f"{self.reference_lists_service.api_root}tabellen?code=broken-table",
            exc=RequestException("something went wrong (Table)"),
        )

        send_email_digest()
        sent_email = mail.outbox[-1]
        assert isinstance(sent_email.body, str)

        self.assertIn(
            f"Something went wrong while trying to retrieve data from service: {self.reference_lists_service.label}",
            sent_email.body,
        )
        self.assertIn(
            "something went wrong (Table)",
            sent_email.body,
        )

    @requests_mock.Mocker()
    def test_exception_for_items_returns_proper_message(self, m):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "label": "Selectboxes",
                        "openForms": {
                            "dataSrc": "referenceLists",
                            "service": "reference-lists",
                            "code": "broken-items",
                        },
                    }
                ],
            },
        )

        m.get(
            f"{self.reference_lists_service.api_root}tabellen?code=broken-items",
            json={
                "results": [
                    {
                        "code": "broken-items",
                        "naam": "Broken items request",
                        "einddatumGeldigheid": None,
                        "beheerder": {
                            "beheerder_naam": "",
                            "beheerder_email": "",
                            "beheerder_afdeling": "",
                            "beheerder_organisatie": "",
                        },
                    }
                ]
            },
        )
        m.get(
            f"{self.reference_lists_service.api_root}items?tabel__code=broken-items",
            exc=RequestException("something went wrong (Items)"),
        )

        send_email_digest()
        sent_email = mail.outbox[-1]
        assert isinstance(sent_email.body, str)

        self.assertIn(
            f"Something went wrong while trying to retrieve data from service: {self.reference_lists_service.label}",
            sent_email.body,
        )
        self.assertIn(
            "something went wrong (Items)",
            sent_email.body,
        )
