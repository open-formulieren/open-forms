from django.test import TestCase

from mozilla_django_oidc_db.registry import register as registry
from mozilla_django_oidc_db.utils import obfuscate_claims

from openforms.utils.tests.keycloak import mock_oidc_client

from ...oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
)


class OIDCPluginsTestCase(TestCase):
    @mock_oidc_client(
        OIDC_DIGID_IDENTIFIER,
        overrides={"options.identity_settings.bsn_claim_path": ["bsn"]},
    )
    def test_obfuscate_claims_digid(self):
        plugin = registry[OIDC_DIGID_IDENTIFIER]

        obfuscated_claims = obfuscate_claims(
            {"bsn": "123456789", "other": "other"}, plugin.get_sensitive_claims()
        )

        self.assertEqual(obfuscated_claims, {"bsn": "*******89", "other": "other"})

    @mock_oidc_client(
        OIDC_DIGID_MACHTIGEN_IDENTIFIER,
        overrides={
            "options.identity_settings.representee_bsn_claim_path": ["aanvrager"],
            "options.identity_settings.authorizee_bsn_claim_path": ["gemachtigde"],
        },
    )
    def test_obfuscate_claims_digid_machtigen(self):
        plugin = registry[OIDC_DIGID_MACHTIGEN_IDENTIFIER]

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

    @mock_oidc_client(
        OIDC_EH_IDENTIFIER,
        overrides={
            "options.identity_settings.legal_subject_claim_path": ["kvk"],
            "options.identity_settings.acting_subject_claim_path": ["ActingSubject"],
            "options.identity_settings.branch_number_claim_path": ["branch"],
        },
    )
    def test_obfuscate_claims_eherkenning(self):
        plugin = registry[OIDC_EH_IDENTIFIER]

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

    @mock_oidc_client(
        OIDC_EH_BEWINDVOERING_IDENTIFIER,
        overrides={
            "options.identity_settings.legal_subject_claim_path": ["kvk"],
            "options.identity_settings.representee_claim_path": ["bsn"],
            "options.identity_settings.acting_subject_claim_path": ["ActingSubject"],
            "options.identity_settings.branch_number_claim_path": ["branch"],
        },
    )
    def test_obfuscate_claims_eherkenning_bewindvoering(self):
        plugin = registry[OIDC_EH_BEWINDVOERING_IDENTIFIER]

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
