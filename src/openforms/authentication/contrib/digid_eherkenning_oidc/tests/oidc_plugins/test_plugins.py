from django.test import TestCase

from mozilla_django_oidc_db.registry import register as oidc_register
from mozilla_django_oidc_db.utils import obfuscate_claims

from openforms.authentication.contrib.digid_eherkenning_oidc.oidc_plugins.plugins import (
    OIDCDigiDMachtigenPlugin,
    OIDCDigidPlugin,
    OIDCeHerkenningBewindvoeringPlugin,
    OIDCeHerkenningPlugin,
    OIDCEidasCompanyPlugin,
    OIDCEidasPlugin,
)
from openforms.contrib.auth_oidc.plugin import OFBaseOIDCPluginProtocol
from openforms.contrib.auth_oidc.tests.factories import (
    OFOIDCClientFactory,
)
from openforms.utils.tests.oidc import OIDCMixin


class OIDCPluginsTestCase(OIDCMixin, TestCase):
    def test_obfuscate_claims_digid(self):
        oidc_client = OFOIDCClientFactory.create(
            with_digid=True,
            options__identity_settings__bsn_claim_path=["bsn"],
        )

        plugin = oidc_register[oidc_client.identifier]

        assert isinstance(plugin, OIDCDigidPlugin)
        assert isinstance(plugin, OFBaseOIDCPluginProtocol)
        obfuscated_claims = obfuscate_claims(
            {"bsn": "123456789", "other": "other"}, plugin.get_sensitive_claims()
        )

        self.assertEqual(obfuscated_claims, {"bsn": "*******89", "other": "other"})

    def test_obfuscate_claims_digid_machtigen(self):
        oidc_client = OFOIDCClientFactory.create(
            with_digid_machtigen=True,
            options__identity_settings__representee_bsn_claim_path=["aanvrager"],
            options__identity_settings__authorizee_bsn_claim_path=["gemachtigde"],
        )

        plugin = oidc_register[oidc_client.identifier]

        assert isinstance(plugin, OIDCDigiDMachtigenPlugin)
        assert isinstance(plugin, OFBaseOIDCPluginProtocol)
        obfuscated_claims = obfuscate_claims(
            {
                "aanvrager": "123456789",
                "gemachtigde": "123456789",
                "other": "other",
            },
            plugin.get_sensitive_claims(),
        )

        self.assertEqual(
            obfuscated_claims,
            {
                "aanvrager": "*******89",
                "gemachtigde": "*******89",
                "other": "other",
            },
        )

    def test_obfuscate_claims_eherkenning(self):
        oidc_client = OFOIDCClientFactory.create(
            with_eherkenning=True,
            options__identity_settings__legal_subject_claim_path=["kvk"],
            options__identity_settings__acting_subject_claim_path=["ActingSubject"],
            options__identity_settings__branch_number_claim_path=["branch"],
        )

        plugin = oidc_register[oidc_client.identifier]

        assert isinstance(plugin, OIDCeHerkenningPlugin)
        assert isinstance(plugin, OFBaseOIDCPluginProtocol)
        obfuscated_claims = obfuscate_claims(
            {
                "kvk": "12345678",
                "branch": "112233445566",
                # this is already obfuscated by the broker
                "ActingSubject": "1234567890@0987654321",
            },
            plugin.get_sensitive_claims(),
        )

        self.assertEqual(
            obfuscated_claims,
            {
                "kvk": "*******8",
                "branch": "**********66",
                # this is already obfuscated by the broker
                "ActingSubject": "1234567890@0987654321",
            },
        )

    def test_obfuscate_claims_eherkenning_bewindvoering(self):
        oidc_client = OFOIDCClientFactory.create(
            with_eherkenning_bewindvoering=True,
            options__identity_settings__legal_subject_claim_path=["kvk"],
            options__identity_settings__representee_claim_path=["bsn"],
            options__identity_settings__acting_subject_claim_path=["ActingSubject"],
            options__identity_settings__branch_number_claim_path=["branch"],
        )

        plugin = oidc_register[oidc_client.identifier]

        assert isinstance(plugin, OIDCeHerkenningBewindvoeringPlugin)
        assert isinstance(plugin, OFBaseOIDCPluginProtocol)
        obfuscated_claims = obfuscate_claims(
            {
                "bsn": "123456789",
                "kvk": "12345678",
                "branch": "112233445566",
                # this is already obfuscated by the broker
                "ActingSubject": "1234567890@0987654321",
            },
            plugin.get_sensitive_claims(),
        )

        self.assertEqual(
            obfuscated_claims,
            {
                "bsn": "*******89",
                "kvk": "*******8",
                "branch": "**********66",
                # this is already obfuscated by the broker
                "ActingSubject": "1234567890@0987654321",
            },
        )

    def test_obfuscate_claims_eidas(self):
        oidc_client = OFOIDCClientFactory.create(
            with_eidas=True,
            options__identity_settings__legal_subject_identifier_claim_path=[
                "person_identifier"
            ],
            options__identity_settings__legal_subject_first_name_claim_path=[
                "first_name"
            ],
            options__identity_settings__legal_subject_family_name_claim_path=[
                "family_name"
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        assert isinstance(plugin, OIDCEidasPlugin)
        assert isinstance(plugin, OFBaseOIDCPluginProtocol)
        obfuscated_claims = obfuscate_claims(
            {
                "person_identifier": "123456789",
                "first_name": "John",
                "family_name": "Doe",
            },
            plugin.get_sensitive_claims(),
        )

        self.assertEqual(
            obfuscated_claims,
            {
                "person_identifier": "*******89",
                "first_name": "****",
                "family_name": "***",
            },
        )

    def test_obfuscate_claims_eidas_company(self):
        oidc_client = OFOIDCClientFactory.create(
            with_eidas_company=True,
            options__identity_settings__legal_subject_identifier_claim_path=[
                "company_identifier"
            ],
            options__identity_settings__acting_subject_identifier_claim_path=[
                "person_identifier"
            ],
            options__identity_settings__acting_subject_first_name_claim_path=[
                "first_name"
            ],
            options__identity_settings__acting_subject_family_name_claim_path=[
                "family_name"
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        assert isinstance(plugin, OIDCEidasCompanyPlugin)
        assert isinstance(plugin, OFBaseOIDCPluginProtocol)
        obfuscated_claims = obfuscate_claims(
            {
                "company_identifier": "123456789",
                "person_identifier": "000111222",
                "family_name": "Doe",
                "first_name": "John",
            },
            plugin.get_sensitive_claims(),
        )

        self.assertEqual(
            obfuscated_claims,
            {
                "person_identifier": "*******22",
                "company_identifier": "*******89",
                "first_name": "****",
                "family_name": "***",
            },
        )
