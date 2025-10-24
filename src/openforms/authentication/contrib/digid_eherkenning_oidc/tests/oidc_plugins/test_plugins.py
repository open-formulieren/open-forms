from django.test import TestCase

from mozilla_django_oidc_db.registry import register as oidc_register
from mozilla_django_oidc_db.tests.mixins import OIDCMixin
from mozilla_django_oidc_db.utils import obfuscate_claims

from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory

from ...oidc_plugins.plugins import BaseDigiDeHerkenningPlugin


class OIDCPluginsTestCase(OIDCMixin, TestCase):
    def test_obfuscate_claims_digid(self):
        oidc_client = OFOIDCClientFactory.create(
            with_digid=True,
            options__identity_settings__bsn_claim_path=["bsn"],
        )

        plugin = oidc_register[oidc_client.identifier]

        assert isinstance(plugin, BaseDigiDeHerkenningPlugin)
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

        assert isinstance(plugin, BaseDigiDeHerkenningPlugin)
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

        assert isinstance(plugin, BaseDigiDeHerkenningPlugin)
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

        assert isinstance(plugin, BaseDigiDeHerkenningPlugin)
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
            options__identity_settings__legal_subject_bsn_identifier_claim_path=[
                "person_bsn_identifier"
            ],
            options__identity_settings__legal_subject_pseudo_identifier_claim_path=[
                "person_pseudo_identifier"
            ],
            options__identity_settings__legal_subject_first_name_claim_path=[
                "first_name"
            ],
            options__identity_settings__legal_subject_family_name_claim_path=[
                "family_name"
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        assert isinstance(plugin, BaseDigiDeHerkenningPlugin)
        obfuscated_claims = obfuscate_claims(
            {
                "person_bsn_identifier": "123456789",
                "person_pseudo_identifier": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                "first_name": "John",
                "family_name": "Doe",
            },
            plugin.get_sensitive_claims(),
        )

        self.assertEqual(
            obfuscated_claims,
            {
                "person_bsn_identifier": "*******89",
                "person_pseudo_identifier": "**********************************************************************************4lvxEzdpgtnzCt5TbKJ4cnd0gL",
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
            options__identity_settings__acting_subject_bsn_identifier_claim_path=[
                "person_bsn_identifier"
            ],
            options__identity_settings__acting_subject_pseudo_identifier_claim_path=[
                "person_pseudo_identifier"
            ],
            options__identity_settings__acting_subject_first_name_claim_path=[
                "first_name"
            ],
            options__identity_settings__acting_subject_family_name_claim_path=[
                "family_name"
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        assert isinstance(plugin, BaseDigiDeHerkenningPlugin)
        obfuscated_claims = obfuscate_claims(
            {
                "company_identifier": "123456789",
                "person_bsn_identifier": "000111222",
                "person_pseudo_identifier": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                "family_name": "Doe",
                "first_name": "John",
            },
            plugin.get_sensitive_claims(),
        )

        self.assertEqual(
            obfuscated_claims,
            {
                "person_bsn_identifier": "*******22",
                "person_pseudo_identifier": "**********************************************************************************4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                "company_identifier": "*******89",
                "first_name": "****",
                "family_name": "***",
            },
        )
