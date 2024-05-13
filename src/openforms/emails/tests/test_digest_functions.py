from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from django.core.files import File
from django.test import TestCase, override_settings
from django.utils.timezone import utc

import requests_mock
from django_yubin.models import Message
from freezegun import freeze_time
from simple_certmanager.test.factories import CertificateFactory
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.brk.models import BRKConfig
from openforms.contrib.brk.tests.base import BRK_SERVICE
from openforms.contrib.kadaster.models import KadasterApiConfig
from openforms.forms.tests.factories import FormFactory
from openforms.logging import logevent
from openforms.prefill.registry import register
from openforms.registrations.exceptions import RegistrationFailed
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.tests.factories import SubmissionFactory
from stuf.stuf_bg.client import NoServiceConfigured

from ..digest import (
    collect_broken_configurations,
    collect_failed_emails,
    collect_failed_prefill_plugins,
    collect_failed_registrations,
    collect_invalid_certificates,
)
from ..tasks import Digest

TEST_FILES = Path(__file__).parent / "data"


@freeze_time("2023-02-02T12:30:00+01:00")
class FailedEmailsTests(TestCase):

    def test_failed_emails_are_collected(self):
        submission = SubmissionFactory.create()

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

        failed_emails = collect_failed_emails(
            since=datetime(2023, 2, 1, 0, 0, 0).replace(tzinfo=utc)
        )

        self.assertEqual(len(failed_emails), 1)
        self.assertEqual(failed_emails[0].submission_uuid, submission.uuid)

    def test_sent_emails_are_not_collected(self):
        submission = SubmissionFactory.create()

        # Log email failed more than 24h ago
        logevent.email_status_change(
            submission,
            event="registration",
            status=Message.STATUS_FAILED,
            status_label="Failed",
            include_in_daily_digest=True,
        )

        failed_emails = collect_failed_emails(
            since=datetime(2023, 2, 2, 13, 30, 0).replace(tzinfo=utc)
        )

        self.assertEqual(failed_emails, [])


@freeze_time("2023-01-02T12:30:00+01:00")
class FailedRegistrationsTests(TestCase):

    def test_failed_registrations_are_collected(self):
        # 1st form with 2 failures in the past 24 hours
        form_1 = FormFactory.create()
        failed_submission_1 = SubmissionFactory.create(
            form=form_1, registration_status=RegistrationStatuses.failed
        )
        failed_submission_2 = SubmissionFactory.create(
            form=form_1, registration_status=RegistrationStatuses.failed
        )

        # 1st failure
        logevent.registration_failure(
            failed_submission_1,
            RegistrationFailed("Registration plugin is not enabled"),
        )

        # 2nd failure
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
        logevent.registration_failure(
            failed_submission,
            RegistrationFailed("Registration plugin is not enabled"),
        )

        failed_registrations = collect_failed_registrations(
            since=datetime(2023, 1, 1, 14, 30, 0).replace(tzinfo=utc)
        )

        self.assertEqual(len(failed_registrations), 2)
        self.assertEqual(failed_registrations[0].failed_submissions_counter, 2)
        self.assertEqual(failed_registrations[1].failed_submissions_counter, 1)

    def test_timestamp_constraint_returns_no_results(self):
        form = FormFactory.create()
        submission = SubmissionFactory.create(form=form, registration_failed=True)

        logevent.registration_failure(
            submission,
            RegistrationFailed("Registration plugin is not enabled"),
        )

        digest = Digest(since=datetime(2023, 1, 4, 1, 0, 0).replace(tzinfo=utc))
        context = digest.get_context_data()

        self.assertEqual(context["failed_emails"], [])


@freeze_time("2023-01-02T12:30:00+01:00")
class FailedPrefillTests(TestCase):

    def test_prefill_plugin_failures_are_collected(self):
        hc_plugin = register["haalcentraal"]
        stufbg_plugin = register["stufbg"]

        # 1st form with 2 failures in the past 24 hours
        form_1 = FormFactory.create()
        submission_1 = SubmissionFactory.create(form=form_1)
        submission_2 = SubmissionFactory.create(form=form_1)

        # 1st failure(no values)
        logevent.prefill_retrieve_empty(
            submission_1, hc_plugin, ["burgerservicenummer"]
        )

        # 2nd failure(no values)
        logevent.prefill_retrieve_empty(
            submission_2, hc_plugin, ["burgerservicenummer"]
        )

        # 2nd form with 1 failure in the past 24 hours
        form_2 = FormFactory.create()
        submission = SubmissionFactory.create(form=form_2)

        # failure(service not configured)
        logevent.prefill_retrieve_failure(
            submission, stufbg_plugin, NoServiceConfigured()
        )

        failed_plugins = collect_failed_prefill_plugins(
            since=datetime(2023, 1, 2, 2, 0, 0).replace(tzinfo=utc)
        )

        self.assertEqual(len(failed_plugins), 2)
        self.assertEqual(failed_plugins[0].failed_submissions_counter, 2)
        self.assertEqual(failed_plugins[1].failed_submissions_counter, 1)

    def test_timestamp_constraint_returns_no_results(self):
        hc_plugin = register["haalcentraal"]

        form = FormFactory.create()
        submission = SubmissionFactory.create(form=form)

        logevent.prefill_retrieve_empty(submission, hc_plugin, ["burgerservicenummer"])

        digest = Digest(since=datetime(2023, 1, 4, 1, 0, 0).replace(tzinfo=utc))
        context = digest.get_context_data()

        self.assertEqual(context["failed_prefill_plugins"], [])


@override_settings(LANGUAGE_CODE="en")
class BrokenConfigurationTests(TestCase):

    @patch(
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=BRK_SERVICE),
    )
    @requests_mock.Mocker()
    def test_valid_brk_congiguration_for_addressNL_not_collected(self, brk_config, m):
        FormFactory.create(
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

        m.get(
            "https://api.brk.kadaster.nl/esd-eto-apikey/bevragen/v2/kadastraalonroerendezaken?postcode=1234AB&huisnummer=1",
            json={"_embedded": {}},
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])

    @patch(
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=None),
    )
    def test_invalid_brk_configuration_for_addressNL_is_collected(self, brk_config):
        FormFactory.create(
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

        broken_configuration = collect_broken_configurations()

        self.assertEqual(len(broken_configuration), 1)
        self.assertEqual(broken_configuration[0].config_name, "BRK Client")

    @patch(
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=None),
    )
    def test_invalid_brk_congiguration_but_unused_not_collected(self, brk_config):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "textField",
                        "type": "textfield",
                        "label": "Text Field",
                    }
                ],
            },
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])

    @patch(
        "openforms.contrib.kadaster.models.KadasterApiConfig.get_solo",
        return_value=KadasterApiConfig(
            search_service=None,
            bag_service=ServiceFactory.build(
                api_root="https://bag/api/",
                oas="https://bag/api/schema/openapi.yaml",
            ),
        ),
    )
    @requests_mock.Mocker()
    def test_valid_bag_configuration_for_address_fields_is_not_sent(self, kd_config, m):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "postCode",
                        "type": "postcode",
                        "label": "Postcode",
                    },
                    {
                        "key": "houseNumber",
                        "type": "textfield",
                        "label": "house number",
                    },
                    {
                        "key": "streetName",
                        "type": "textfield",
                        "label": "Street name",
                        "deriveCity": False,
                        "derivePostcode": "postCode",
                        "deriveStreetName": True,
                        "deriveHouseNumber": "houseNumber",
                    },
                ],
            },
        )

        m.get(
            "https://bag/api/adressen?postcode=1000AA&huisnummer=1",
            status_code=200,
            json={},
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])

    @patch("openforms.contrib.kadaster.models.KadasterApiConfig.get_solo")
    def test_invalid_bag_configuration_for_address_fields_is_collected(self, kd_config):
        kd_config.return_value = KadasterApiConfig(bag_service=None)

        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "postCode",
                        "type": "postcode",
                        "label": "Postcode",
                    },
                    {
                        "key": "houseNumber",
                        "type": "textfield",
                        "label": "house number",
                    },
                    {
                        "key": "streetName",
                        "type": "textfield",
                        "label": "Street name",
                        "deriveCity": False,
                        "derivePostcode": "postCode",
                        "deriveStreetName": True,
                        "deriveHouseNumber": "houseNumber",
                    },
                ]
            },
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(len(broken_configuration), 1)
        self.assertEqual(broken_configuration[0].config_name, "BAG Client")

    @patch("openforms.contrib.kadaster.models.KadasterApiConfig.get_solo")
    def test_invalid_bag_configuration_without_required_property_is_not_collected(
        self, kd_config
    ):
        kd_config.return_value = KadasterApiConfig(bag_service=None)

        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "houseNumber",
                        "type": "textfield",
                        "label": "house number",
                    },
                    {
                        "key": "postCode",
                        "type": "postcode",
                        "label": "Postcode",
                    },
                ],
            },
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])


@override_settings(LANGUAGE_CODE="en")
class InvalidCertificatesTests(TestCase):

    def test_expiring_certificates_not_used_by_a_service_are_not_collected(self):
        # the certificate (test.certificate) expires on Apr 22 13:02:55 2025 GMT
        with open(TEST_FILES / "test.certificate", "r") as client_certificate_f:
            CertificateFactory.create(
                label="Test certificate",
                public_certificate=File(client_certificate_f, name="test.certificate"),
            )

        with freeze_time("2025-04-15T21:15:00Z"):
            invalid_certificates = collect_invalid_certificates()

        self.assertEqual(len(invalid_certificates), 0)

    def test_not_expiring_and_valid_certificates_are_not_collected(self):
        # the certificate (test.certificate) expires on Apr 22 13:02:55 2025 GMT
        with open(TEST_FILES / "test.certificate", "r") as client_certificate_f:
            certificate = CertificateFactory.create(
                label="Test certificate",
                public_certificate=File(client_certificate_f, name="test.certificate"),
            )
            ServiceFactory.create(client_certificate=certificate)

        with freeze_time("2024-04-15T21:15:00Z"):
            invalid_certificates = collect_invalid_certificates()

        self.assertEqual(len(invalid_certificates), 0)

    def test_expiring_certificates_are_collected(self):
        # the certificate (test.certificate) expires on Apr 22 13:02:55 2025 GMT
        with open(TEST_FILES / "test.certificate", "r") as client_certificate_f:
            certificate = CertificateFactory.create(
                label="Test certificate",
                public_certificate=File(client_certificate_f, name="test.certificate"),
            )
            ServiceFactory.create(client_certificate=certificate)

        with freeze_time("2025-04-15T21:15:00Z"):
            invalid_certificates = collect_invalid_certificates()

        self.assertEqual(len(invalid_certificates), 1)
        self.assertEqual(invalid_certificates[0].error_message, "will expire soon")

    def test_invalid_certificates_are_collected(self):
        # the certificate (test.certificate) expires on Apr 22 13:02:55 2025 GMT and
        # test2.certificate on Apr 22 13:05:26 2025 GMT. Here the test.key is not valid
        # for test2.certificate which causes an invalid keypair error
        with (
            open(TEST_FILES / "test2.certificate", "r") as client_certificate_f,
            open(TEST_FILES / "test.key", "r") as key_f,
        ):
            certificate = CertificateFactory.create(
                label="Test certificate",
                public_certificate=File(client_certificate_f, name="test.certificate"),
                private_key=File(key_f, name="test.key"),
            )
            ServiceFactory.create(client_certificate=certificate)

        invalid_certificates = collect_invalid_certificates()

        self.assertEqual(len(invalid_certificates), 1)
        self.assertEqual(invalid_certificates[0].error_message, "has invalid keypair")

    def test_both_expiring_and_invalid_certificates_are_collected(self):
        # the certificate (test.certificate) expires on Apr 22 13:02:55 2025 GMT and
        # test2.certificate on Apr 22 13:05:26 2025 GMT. Here the test.key is not valid
        # for test2.certificate which causes an invalid keypair error
        with (
            open(TEST_FILES / "test2.certificate", "r") as client_certificate_f,
            open(TEST_FILES / "test.key", "r") as key_f,
        ):
            certificate = CertificateFactory.create(
                label="Test certificate",
                public_certificate=File(client_certificate_f, name="test.certificate"),
                private_key=File(key_f, name="test.key"),
            )
            ServiceFactory.create(client_certificate=certificate)

        with freeze_time("2025-04-15T21:15:00Z"):
            invalid_certificates = collect_invalid_certificates()

        self.assertEqual(len(invalid_certificates), 1)
        self.assertEqual(
            invalid_certificates[0].error_message, "invalid keypair, will expire soon"
        )
