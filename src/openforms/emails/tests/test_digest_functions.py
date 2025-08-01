from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from django.core.files import File
from django.test import TestCase, override_settings, tag
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_yubin.models import Message
from freezegun import freeze_time
from rest_framework import serializers
from simple_certmanager.test.factories import CertificateFactory
from zgw_consumers.test.factories import ServiceFactory

from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.contrib.brk.models import BRKConfig
from openforms.contrib.brk.tests.base import BRK_SERVICE, INVALID_BRK_SERVICE
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.contrib.kadaster.models import KadasterApiConfig
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormVariableFactory,
)
from openforms.logging import logevent
from openforms.logging.models import TimelineLogProxy
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.prefill.registry import register as prefill_register
from openforms.registrations.base import BasePlugin
from openforms.registrations.exceptions import RegistrationFailed
from openforms.registrations.registry import register as register_register
from openforms.submissions.constants import RegistrationStatuses
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes
from stuf.stuf_bg.client import NoServiceConfigured
from stuf.stuf_bg.models import StufBGConfig

from ..digest import (
    InvalidLogicRule,
    collect_broken_configurations,
    collect_expired_or_near_expiry_reference_lists_data,
    collect_failed_emails,
    collect_failed_prefill_plugins,
    collect_failed_registrations,
    collect_invalid_certificates,
    collect_invalid_logic_rules,
    collect_invalid_registration_backends,
)
from ..tasks import Digest

utc = UTC

TEST_FILES = Path(__file__).parent / "data"


class UnexpectedError(Exception): ...


class OptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    def validate(self, attrs):
        raise serializers.ValidationError("Invalid configuration")


class ErrorOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    def validate(self, attrs):
        raise UnexpectedError("Something bad happened")


@register_register("test-invalid-backend")
class InvalidBackend(BasePlugin):
    verbose_name = "Invalid backend"

    def register_submission(self, submission, options):
        pass

    def check_config(self):
        raise InvalidPluginConfiguration("Invalid")


@register_register("test-invalid-form-conf")
class InvalidFormConfiguration(BasePlugin):
    verbose_name = "Invalid form configuration"
    configuration_options = OptionsSerializer

    def register_submission(self, submission, options):
        pass

    def check_config(self):
        pass


@register_register("test-error-form-conf")
class ErrorFormConfiguration(BasePlugin):
    verbose_name = "Error form configuration"
    configuration_options = ErrorOptionsSerializer

    def register_submission(self, submission, options):
        pass

    def check_config(self):
        pass


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
        hc_plugin = prefill_register["haalcentraal"]
        stufbg_plugin = prefill_register["stufbg"]

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
        hc_plugin = prefill_register["haalcentraal"]

        form = FormFactory.create()
        submission = SubmissionFactory.create(form=form)

        logevent.prefill_retrieve_empty(submission, hc_plugin, ["burgerservicenummer"])

        digest = Digest(since=datetime(2023, 1, 4, 1, 0, 0).replace(tzinfo=utc))
        context = digest.get_context_data()

        self.assertEqual(context["failed_prefill_plugins"], [])


@override_settings(LANGUAGE_CODE="en")
class BrokenConfigurationTests(TestCase):
    def test_no_addressNL_component_not_collected(self):
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
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=None),
    )
    def test_no_brk_conf_for_addressnl_and_missing_validator_not_collected(self, m):
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

        self.assertEqual(broken_configuration, [])

    @patch(
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=None),
    )
    def test_no_brk_conf_for_addressnl_and_existing_validator_not_collected(self, m):
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
                        "validate": {"plugins": ["brk-zakelijk-gerechtigd"]},
                    }
                ],
            },
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])

    @patch(
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=BRK_SERVICE),
    )
    def test_valid_brk_conf_for_addressnl_and_missing_validator_not_collected(
        self, brk_config
    ):
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

        self.assertEqual(broken_configuration, [])

    @patch(
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=BRK_SERVICE),
    )
    @requests_mock.Mocker()
    def test_valid_brk_conf_for_addressnl_and_existing_validator_not_collected(
        self, brk_config, m
    ):
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
                        "validate": {"plugins": ["brk-zakelijk-gerechtigd"]},
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
        return_value=BRKConfig(service=INVALID_BRK_SERVICE),
    )
    def test_invalid_brk_conf_for_addressnl_and_missing_validator_not_collected(
        self, brk_config
    ):
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

        self.assertEqual(broken_configuration, [])

    @patch(
        "openforms.contrib.brk.client.BRKConfig.get_solo",
        return_value=BRKConfig(service=INVALID_BRK_SERVICE),
    )
    @requests_mock.Mocker()
    def test_invalid_brk_conf_for_addressnl_and_existing_validator_collected(
        self, brk_config, m
    ):
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
                        "validate": {"plugins": ["brk-zakelijk-gerechtigd"]},
                    }
                ],
            },
        )

        m.get(
            "https://api.brk.kadaster.nl/invalid/kadastraalonroerendezaken?postcode=1234AB&huisnummer=1",
            status_code=400,
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(len(broken_configuration), 1)
        self.assertEqual(broken_configuration[0].config_name, "BRK Client")

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

    @patch("openforms.contrib.kadaster.models.KadasterApiConfig.get_solo")
    def test_invalid_bag_configuration_for_address_nl_component_is_collected(
        self, kd_config
    ):
        kd_config.return_value = KadasterApiConfig(bag_service=None)

        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "addressNl",
                        "type": "addressNL",
                        "label": "Address NL",
                        "deriveAddress": True,
                    }
                ]
            },
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(len(broken_configuration), 1)
        self.assertEqual(broken_configuration[0].config_name, "BAG Client")

    @patch("openforms.contrib.kadaster.models.KadasterApiConfig.get_solo")
    def test_invalid_bag_configuration_for_address_nl_component_not_collected_when_disabled(
        self, kd_config
    ):
        kd_config.return_value = KadasterApiConfig(bag_service=None)

        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "addressNl",
                        "type": "addressNL",
                        "label": "Address NL",
                        "deriveAddress": False,
                    }
                ]
            },
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(len(broken_configuration), 0)

    @patch(
        "stuf.stuf_bg.client.StufBGConfig.get_solo",
        return_value=StufBGConfig(service=None),
    )
    @patch(
        "openforms.prefill.contrib.family_members.plugin.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.stuf_bg
        ),
    )
    def test_family_members_with_no_stufbg_service_collected(self, m, n):
        with self.subTest("partners"):
            form = FormFactory.create(
                generate_minimal_setup=True,
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "key": "partners",
                            "type": "partners",
                            "label": "Partners",
                        }
                    ],
                },
            )
            FormVariableFactory.create(
                form=form,
                user_defined=True,
                key="immutable_partners",
                data_type=FormVariableDataTypes.array,
                prefill_plugin="family_members",
                prefill_options={
                    "type": "partners",
                    "mutable_data_form_variable": "partners",
                },
                initial_value=[
                    {
                        "bsn": "123456782",
                        "initials": "",
                        "affixes": "L",
                        "lastName": "Boei",
                        "dateOfBirth": "1990-01-01",
                    }
                ],
            )

            broken_configuration = collect_broken_configurations()

            self.assertEqual(len(broken_configuration), 1)
            self.assertEqual(broken_configuration[0].config_name, "StUF-BG Client")

        with self.subTest("children"):
            form = FormFactory.create(
                generate_minimal_setup=True,
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "key": "children",
                            "type": "children",
                            "label": "Children",
                            "enableSelection": False,
                        }
                    ],
                },
            )
            FormVariableFactory.create(
                form=form,
                user_defined=True,
                key="immutable_children",
                data_type=FormVariableDataTypes.array,
                prefill_plugin="family_members",
                prefill_options={
                    "type": "children",
                    "mutable_data_form_variable": "children",
                },
                initial_value=[
                    {
                        "bsn": "999970409",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                    }
                ],
            )

            broken_configuration = collect_broken_configurations()

            self.assertEqual(len(broken_configuration), 1)
            self.assertEqual(broken_configuration[0].config_name, "StUF-BG Client")

    @patch(
        "openforms.prefill.contrib.family_members.plugin.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(family_members_data_api=""),
    )
    def test_family_members_and_no_client_for_retrieving_data_configured_not_collected(
        self, m
    ):
        with self.subTest("partners"):
            form = FormFactory.create(
                generate_minimal_setup=True,
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "key": "partners",
                            "type": "partners",
                            "label": "Partners",
                        }
                    ],
                },
            )
            FormVariableFactory.create(
                form=form,
                user_defined=True,
                key="immutable_partners",
                data_type=FormVariableDataTypes.array,
                prefill_plugin="family_members",
                prefill_options={
                    "type": "partners",
                    "mutable_data_form_variable": "partners",
                },
                initial_value=[
                    {
                        "bsn": "123456782",
                        "initials": "",
                        "affixes": "L",
                        "lastName": "Boei",
                        "dateOfBirth": "1990-01-01",
                    }
                ],
            )

            broken_configuration = collect_broken_configurations()

            self.assertEqual(broken_configuration, [])

        with self.subTest("children"):
            form = FormFactory.create(
                generate_minimal_setup=True,
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "key": "children",
                            "type": "children",
                            "label": "Children",
                            "enableSelection": False,
                        }
                    ],
                },
            )
            FormVariableFactory.create(
                form=form,
                user_defined=True,
                key="immutable_children",
                data_type=FormVariableDataTypes.array,
                prefill_plugin="family_members",
                prefill_options={
                    "type": "children",
                    "mutable_data_form_variable": "children",
                },
                initial_value=[
                    {
                        "bsn": "999970409",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                    }
                ],
            )

            broken_configuration = collect_broken_configurations()

            self.assertEqual(broken_configuration, [])

    def test_no_partners_component_with_immutable_variable_collected(self):
        form = FormFactory.create(
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

        FormVariableFactory.create(
            form=form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration[0].config_name, "User defined Variables")

    def test_no_children_component_with_immutable_variable_collected(self):
        form = FormFactory.create(
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

        FormVariableFactory.create(
            form=form,
            user_defined=True,
            key="immutable_children",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "dateOfBirth": "2023-02-01",
                }
            ],
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration[0].config_name, "User defined Variables")

    @patch(
        "openforms.prefill.contrib.family_members.plugin.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.stuf_bg
        ),
    )
    def test_stufbg_partners_component_without_immutable_variable_not_collected(
        self, m
    ):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "partners",
                        "type": "partners",
                        "label": "Partners",
                    }
                ],
            },
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])

    @patch(
        "openforms.prefill.contrib.family_members.plugin.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.stuf_bg
        ),
    )
    def test_stufbg_children_component_without_immutable_variable_not_collected(
        self, m
    ):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "children",
                        "type": "children",
                        "label": "Children",
                        "enableSelection": False,
                    }
                ],
            },
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])

    def test_partners_component_with_immutable_variable_not_collected(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "partners",
                        "type": "partners",
                        "label": "Partners",
                    }
                ],
            },
        )

        FormVariableFactory.create(
            form=form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])

    def test_children_component_with_immutable_variable_not_collected(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "children",
                        "type": "children",
                        "label": "Children",
                        "enableSelection": False,
                    }
                ],
            },
        )

        FormVariableFactory.create(
            form=form,
            user_defined=True,
            key="immutable_children",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "dateOfBirth": "2023-02-01",
                }
            ],
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])

    def test_same_component_key_as_mutable_in_two_forms(self):
        """
        This is covering the case where we may have two different forms which have the same
        key for the mutable varible/component (configured in the user defined immutable
        variable). We make sure that the form which has broken configuration is reported.
        """
        form1 = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "children",
                        "type": "children",
                        "label": "Children",
                        "enableSelection": False,
                    }
                ],
            },
        )
        form2 = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [],
            },
        )

        FormVariableFactory.create(
            form=form1,
            user_defined=True,
            key="immutable_children",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "dateOfBirth": "2023-02-01",
                }
            ],
        )
        user_defined_2 = FormVariableFactory.create(
            form=form2,
            user_defined=True,
            key="immutable_children_2",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "dateOfBirth": "2023-02-01",
                }
            ],
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(
            broken_configuration[0].exception_message,
            _(
                "There is no component of type 'partners/children' connected to variables '{user_defined}'."
            ).format(user_defined=user_defined_2.name),
        )


@override_settings(LANGUAGE_CODE="en")
class FamilyMembersBrokenHCConfigurationTests(OFVCRMixin, TestCase):
    """This test case requires the HaalCentraal BRP API to be running.
    See the relevant Docker compose in the ``docker/`` folder.

    Note: please ensure that all patches to the test data have been applied. See the
    README.md file of the relevant container.
    """

    VCR_TEST_FILES = TEST_FILES

    def setUp(self):
        super().setUp()

        self.hc_config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="http://localhost:5010/haalcentraal/api/brp/"
            ),
            brp_personen_version=BRPVersions.v20,
        )
        hc_config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=self.hc_config,
        )
        global_config = GlobalConfiguration(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        )
        global_config_patcher = patch(
            "openforms.config.models.GlobalConfiguration.get_solo",
            return_value=global_config,
        )
        hc_config_patcher.start()
        global_config_patcher.start()
        self.addCleanup(hc_config_patcher.stop)
        self.addCleanup(global_config_patcher.stop)

    def test_partners_with_no_hc_service_collected(self):
        self.hc_config.brp_personen_service = None
        self.hc_config.brp_personen_version = ""
        self.hc_config.save()

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "partners",
                        "type": "partners",
                        "label": "partners",
                    }
                ],
            },
        )
        FormVariableFactory.create(
            form=form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(len(broken_configuration), 1)
        self.assertEqual(broken_configuration[0].config_name, "Haal centraal Client")

    def test_partners_with_hc_and_immutable_variable_not_collected(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "partners",
                        "type": "partners",
                        "label": "partners",
                    }
                ],
            },
        )
        FormVariableFactory.create(
            form=form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])

    def test_partners_with_hc_and_no_immutable_variable_not_collected(self):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "partners",
                        "type": "partners",
                        "label": "partners",
                    }
                ],
            },
        )

        broken_configuration = collect_broken_configurations()

        self.assertEqual(broken_configuration, [])


@override_settings(LANGUAGE_CODE="en")
class InvalidCertificatesTests(TestCase):
    def test_expiring_certificates_not_used_by_a_service_are_not_collected(self):
        # the certificate (test.certificate) expires on Apr 9 05:17:53 2026 GMT
        with open(TEST_FILES / "test.certificate") as client_certificate_f:
            CertificateFactory.create(
                label="Test certificate",
                public_certificate=File(client_certificate_f, name="test.certificate"),
            )

        with freeze_time("2026-04-01T21:15:00Z"):
            invalid_certificates = collect_invalid_certificates()

        self.assertEqual(len(invalid_certificates), 0)

    def test_not_expiring_and_valid_certificates_are_not_collected(self):
        # the certificate (test.certificate) expires on Apr 9 05:17:53 2026 GMT
        with open(TEST_FILES / "test.certificate") as client_certificate_f:
            certificate = CertificateFactory.create(
                label="Test certificate",
                public_certificate=File(client_certificate_f, name="test.certificate"),
            )
            ServiceFactory.create(client_certificate=certificate)

        with freeze_time("2024-04-15T21:15:00Z"):
            invalid_certificates = collect_invalid_certificates()

        self.assertEqual(len(invalid_certificates), 0)

    def test_expiring_certificates_are_collected(self):
        # the certificate (test.certificate) expires on Apr 9 05:17:53 2026 GMT
        with open(TEST_FILES / "test.certificate") as client_certificate_f:
            certificate = CertificateFactory.create(
                label="Test certificate",
                public_certificate=File(client_certificate_f, name="test.certificate"),
            )
            ServiceFactory.create(client_certificate=certificate)

        with freeze_time("2026-04-01T21:15:00Z"):
            invalid_certificates = collect_invalid_certificates()

        self.assertEqual(len(invalid_certificates), 1)
        self.assertEqual(invalid_certificates[0].error_message, "will expire soon")

    def test_invalid_certificates_are_collected(self):
        # the certificate (test.certificate) expires on Apr 9 05:17:53 2026 GMT and
        # test2.certificate on Apr 9 05:22:12 2026 GMT. Here the test.key is not valid
        # for test2.certificate which causes an invalid keypair error
        with (
            open(TEST_FILES / "test2.certificate") as client_certificate_f,
            open(TEST_FILES / "test.key") as key_f,
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
        # the certificate (test.certificate) expires on Apr 9 05:17:53 2026 GMT and
        # test2.certificate on Apr 9 05:22:12 2026 GMT. Here the test.key is not valid
        # for test2.certificate which causes an invalid keypair error
        with (
            open(TEST_FILES / "test2.certificate") as client_certificate_f,
            open(TEST_FILES / "test.key") as key_f,
        ):
            certificate = CertificateFactory.create(
                label="Test certificate",
                public_certificate=File(client_certificate_f, name="test.certificate"),
                private_key=File(key_f, name="test.key"),
            )
            ServiceFactory.create(client_certificate=certificate)

        with freeze_time("2026-04-01T21:15:00Z"):
            invalid_certificates = collect_invalid_certificates()

        self.assertEqual(len(invalid_certificates), 1)
        self.assertEqual(
            invalid_certificates[0].error_message, "invalid keypair, will expire soon"
        )


class InvalidRegistrationBackendsTests(TestCase):
    def test_invalid_general_registration_backend_is_collected(self):
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="plugin1",
            backend="test-invalid-backend",
        )

        invalid_registration_backends = collect_invalid_registration_backends()

        self.assertEqual(len(invalid_registration_backends), 1)
        self.assertEqual(
            invalid_registration_backends[0].config_name, InvalidBackend.verbose_name
        )
        self.assertEqual(invalid_registration_backends[0].form_id, form.id)

    def test_invalid_registration_backend_at_form_level_is_collected(self):
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="plugin1",
            backend="test-invalid-form-conf",
        )

        invalid_registration_backends = collect_invalid_registration_backends()

        self.assertEqual(len(invalid_registration_backends), 1)
        self.assertEqual(
            invalid_registration_backends[0].config_name,
            InvalidFormConfiguration.verbose_name,
        )
        self.assertEqual(invalid_registration_backends[0].form_id, form.id)

    def test_invalid_registration_backend_at_both_general_and_form_level_is_collected(
        self,
    ):
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="plugin1",
            backend="test-invalid-backend",
        )
        FormRegistrationBackendFactory.create(
            form=form,
            key="plugin2",
            backend="test-invalid-form-conf",
        )

        invalid_registration_backends = collect_invalid_registration_backends()

        self.assertEqual(len(invalid_registration_backends), 2)
        self.assertEqual(
            invalid_registration_backends[0].config_name,
            InvalidBackend.verbose_name,
        )
        self.assertEqual(invalid_registration_backends[0].form_id, form.id)
        self.assertEqual(
            invalid_registration_backends[1].config_name,
            InvalidFormConfiguration.verbose_name,
        )
        self.assertEqual(invalid_registration_backends[1].form_id, form.id)

    def test_invalid_registration_backend_is_not_collected_when_form_unavailable(self):
        form = FormFactory.create(active=False)
        FormRegistrationBackendFactory.create(
            form=form,
            key="plugin1",
            backend="test-invalid-backend",
        )

        invalid_registration_backends = collect_invalid_registration_backends()

        self.assertEqual(len(invalid_registration_backends), 0)

    @tag("gh-5340")
    def test_registration_backend_raises_error_during_validation(self):
        form = FormFactory.create()
        FormRegistrationBackendFactory.create(
            form=form,
            key="plugin2",
            backend="test-error-form-conf",
        )

        invalid_registration_backends = collect_invalid_registration_backends()

        self.assertEqual(len(invalid_registration_backends), 1)
        self.assertEqual(
            invalid_registration_backends[0].config_name,
            ErrorFormConfiguration.verbose_name,
        )
        self.assertEqual(invalid_registration_backends[0].form_id, form.id)


class InvalidLogicRulesTests(TestCase):
    def test_valid_logic_rules_are_not_collected_and_not_logged(self):
        form = FormFactory.create()
        FormVariableFactory.create(
            form=form,
            name="Variable 1",
            key="foo",
            user_defined=True,
        )
        FormLogicFactory(
            form=form,
            json_logic_trigger={"==": [{"var": "foo"}, "apple"]},
        )

        invalid_logic_rules = collect_invalid_logic_rules()

        logs_exist = TimelineLogProxy.objects.exists()

        self.assertEqual(len(invalid_logic_rules), 0)
        self.assertFalse(logs_exist)

    def test_invalid_logic_rules_with_nested_key_are_not_reported(self):
        form = FormFactory.create()
        FormVariableFactory.create(
            form=form,
            name="Variable 1",
            key="foo",
            user_defined=True,
            data_type=FormVariableDataTypes.object,
        )
        FormLogicFactory(
            form=form,
            json_logic_trigger={
                "and": [
                    {"<": [{"var": "foo.bar"}, "apple"]},
                    {"<": [{"var": "foo.0.bar"}, "apple"]},
                ]
            },
            actions=[
                {
                    "action": {"type": "variable", "value": "d"},
                    "variable": "foo.wrong",
                    "component": "",
                    "form_step": "",
                    "form_step_uuid": "c490b80f-05fe-4006-884d-f631c8abe968",
                },
            ],
        )

        invalid_logic_rules = collect_invalid_logic_rules()

        self.assertEqual(invalid_logic_rules, [])

    def test_invalid_logic_rules_are_collected_and_not_logged(self):
        form = FormFactory.create()
        FormVariableFactory.create(
            form=form,
            name="Variable str",
            key="fooStr",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
        )
        FormVariableFactory.create(
            form=form,
            name="Variable array",
            key="fooArray",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
        )
        FormLogicFactory(
            form=form,
            json_logic_trigger={
                "and": [
                    {"<": [{"var": "temp"}, 110]},
                    {">": [{"var": "fooStr.nested"}, 110]},
                    {">": [{"var": "fooArray.bar"}, 110]},
                    {"<": [{"var": "temp.0.other"}, 110]},
                    {"<": [{"var": {"var": "another"}}, 110]},
                    {"<": [{"var": ""}, 110]},
                    {"==": [{"var": "pie.filling"}, "apple"]},
                ]
            },
            actions=[
                {
                    "action": {"type": "variable", "value": "d"},
                    "variable": "foo.wrong",
                    "component": "",
                    "form_step": "",
                    "form_step_uuid": "c490b80f-05fe-4006-884d-f631c8abe968",
                },
            ],
        )

        with self.assertNoLogs():
            invalid_logic_rules = collect_invalid_logic_rules()

        self.assertEqual(len(invalid_logic_rules), 8)
        self.assertIn(
            InvalidLogicRule(
                variable="temp", form_name=form.admin_name, form_id=form.id
            ),
            invalid_logic_rules,
        )
        self.assertIn(
            InvalidLogicRule(
                variable="fooStr.nested", form_name=form.admin_name, form_id=form.id
            ),
            invalid_logic_rules,
        )
        self.assertIn(
            InvalidLogicRule(
                variable="fooArray.bar", form_name=form.admin_name, form_id=form.id
            ),
            invalid_logic_rules,
        )
        self.assertIn(
            InvalidLogicRule(
                variable="foo.wrong", form_name=form.admin_name, form_id=form.id
            ),
            invalid_logic_rules,
        )
        self.assertIn(
            InvalidLogicRule(
                variable="temp.0.other", form_name=form.admin_name, form_id=form.id
            ),
            invalid_logic_rules,
        )
        self.assertIn(
            InvalidLogicRule(
                variable="another", form_name=form.admin_name, form_id=form.id
            ),
            invalid_logic_rules,
        )
        self.assertIn(
            InvalidLogicRule(variable="", form_name=form.admin_name, form_id=form.id),
            invalid_logic_rules,
        )
        self.assertIn(
            InvalidLogicRule(
                variable="pie.filling", form_name=form.admin_name, form_id=form.id
            ),
            invalid_logic_rules,
        )

    @tag("gh-4400")
    def test_invalid_logic_rules_with_exceptions_are_reported(self):
        form = FormFactory.create()
        FormLogicFactory(
            form=form,
            json_logic_trigger={"custom_operator": [5, 3]},
            actions=[],
        )

        invalid_logic_rules = collect_invalid_logic_rules()

        self.assertEqual(len(invalid_logic_rules), 1)
        self.assertIn(
            InvalidLogicRule(
                variable="",
                form_name=form.admin_name,
                form_id=form.id,
                exception=True,
                rule_index=1,
            ),
            invalid_logic_rules,
        )

    @tag("gh-4400")
    def test_invalid_logic_actions_with_exceptions_are_reported(self):
        form = FormFactory.create()
        FormVariableFactory.create(
            form=form,
            name="Variable 1",
            key="foo",
            user_defined=True,
        )
        FormLogicFactory(
            form=form,
            json_logic_trigger={"==": [{"var": "foo"}, "apple"]},
            actions=[
                {
                    "action": {
                        "type": "variable",
                        "value": {"custom_operator": [5, 3]},
                    },
                    "variable": "temp",
                    "component": "",
                    "form_step": "",
                    "form_step_uuid": "c490b80f-05fe-4006-884d-f631c8abe968",
                },
            ],
        )

        invalid_logic_rules = collect_invalid_logic_rules()

        self.assertEqual(len(invalid_logic_rules), 1)
        self.assertIn(
            InvalidLogicRule(
                variable="",
                form_name=form.admin_name,
                form_id=form.id,
                exception=True,
                rule_index=1,
            ),
            invalid_logic_rules,
        )

    @tag("gh-5271")
    def test_valid_logic_rules_with_reduce_and_accumulator_not_reported(self):
        form = FormFactory.create()
        FormVariableFactory.create(
            form=form,
            name="Pets",
            key="pets",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
        )
        FormLogicFactory(
            form=form,
            json_logic_trigger={
                ">": [
                    {
                        "reduce": [
                            {"var": "pets"},
                            {"+": [{"var": "accumulator"}, 1]},
                            0,
                        ]
                    },
                    1,
                ]
            },
        )

        invalid_logic_rules = collect_invalid_logic_rules()

        self.assertEqual(len(invalid_logic_rules), 0)

    @tag("gh-5271")
    def test_valid_logic_rules_with_accumulator_without_reduce_not_reported(self):
        form = FormFactory.create()
        FormVariableFactory.create(
            form=form,
            name="Accumulator",
            key="accumulator",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
        )
        FormLogicFactory(
            form=form,
            json_logic_trigger={">": [{"var": "accumulator"}, 1]},
        )

        invalid_logic_rules = collect_invalid_logic_rules()

        self.assertEqual(len(invalid_logic_rules), 0)

    @tag("gh-5271")
    def test_invalid_logic_rules_with_accumulator_without_reduce_reported(self):
        form = FormFactory.create()
        FormVariableFactory.create(
            form=form,
            name="Pet",
            key="pet",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
        )
        FormLogicFactory(
            form=form,
            json_logic_trigger={">": [{"var": "accumulator"}, 1]},
        )

        invalid_logic_rules = collect_invalid_logic_rules()

        self.assertEqual(len(invalid_logic_rules), 1)


class ReferencelistExpiredDataTests(TestCase):
    def test_inactive_form_does_not_trigger_checks(self):
        FormFactory.create(active=False)

        expired_data = collect_expired_or_near_expiry_reference_lists_data()

        self.assertEqual(len(expired_data), 0)

    def test_soft_deleted_form_does_not_trigger_checks(self):
        FormFactory.create(_is_deleted=True)

        expired_data = collect_expired_or_near_expiry_reference_lists_data()

        self.assertEqual(len(expired_data), 0)

    def test_form_with_different_component_does_not_trigger_checks(self):
        FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "textbox",
                        "type": "textbox",
                        "label": "Textbox",
                    }
                ],
            },
        )

        expired_data = collect_expired_or_near_expiry_reference_lists_data()

        self.assertEqual(len(expired_data), 0)
