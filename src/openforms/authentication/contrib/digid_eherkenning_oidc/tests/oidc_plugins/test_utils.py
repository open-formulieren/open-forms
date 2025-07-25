from django.test import TestCase

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from mozilla_django_oidc_db.registry import register as registry
from mozilla_django_oidc_db.tests.factories import (
    OIDCClientFactory,
)

from openforms.utils.tests.keycloak import mock_oidc_client

from ...oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
)
from ...oidc_plugins.types import ClaimProcessingInstructions
from ...oidc_plugins.utils import process_claims


class ProcessClaimsDigiDTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.plugin = registry[OIDC_DIGID_IDENTIFIER]

    @mock_oidc_client(
        OIDC_DIGID_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["sub"],
            "options.loa_settings": {
                "claim_path": ["authsp_level"],
                "default": DigiDAssuranceLevels.middle,
                "value_mapping": [
                    {"from": "30", "to": DigiDAssuranceLevels.high},
                ],
            },
        },
    )
    def test_digid_process_claims(self):
        with self.subTest("BSN extraction + transform loa values"):
            claims = {"sub": "XXXXXXX54", "authsp_level": "30", "extra": "irrelevant"}

            processed_claims = process_claims(
                claims,
                self.plugin.get_claim_processing_instructions(),
                False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "bsn_claim": "XXXXXXX54",
                    "loa_claim": DigiDAssuranceLevels.high,
                },
            )

        with self.subTest("BSN extraction + missing loa claim"):
            claims = {"sub": "XXXXXXX54"}

            processed_claims = process_claims(
                claims,
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "bsn_claim": "XXXXXXX54",
                    "loa_claim": DigiDAssuranceLevels.middle,
                },
            )

        with self.subTest("BSN extraction + unmapped LOA value"):
            claims = {"sub": "XXXXXXX54", "authsp_level": "20", "extra": "irrelevant"}

            processed_claims = process_claims(
                claims,
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "bsn_claim": "XXXXXXX54",
                    "loa_claim": "20",
                },
            )

    @mock_oidc_client(
        OIDC_DIGID_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["sub"],
            "options.loa_settings.claim_path": ["authsp_level"],
        },
    )
    def test_digid_raises_on_missing_claims(self):
        with self.assertRaises(ValueError):
            process_claims(
                {"bsn": "XXXXXXX54"},
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

    @mock_oidc_client(
        OIDC_DIGID_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["sub"],
            "options.loa_settings.claim_path": ["authsp_level"],
            "options.loa_settings.default": "",
        },
    )
    def test_digid_loa_claim_absent_without_default_loa(self):
        processed_claims = process_claims(
            {"sub": "XXXXXXX54"},
            self.plugin.get_claim_processing_instructions(),
            strict=False,
        )

        self.assertEqual(processed_claims, {"bsn_claim": "XXXXXXX54"})

    @mock_oidc_client(
        OIDC_DIGID_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["bsn"],
            "options.loa_settings.claim_path": ["not-present"],
            "options.loa_settings.default": DigiDAssuranceLevels.middle,
        },
    )
    def test_digid_loa_claim_not_configured_but_default_set(self):
        processed_claims = process_claims(
            {"bsn": "XXXXXXX54", "loa": "ignored"},
            self.plugin.get_claim_processing_instructions(),
            strict=False,
        )

        self.assertEqual(
            processed_claims,
            {"bsn_claim": "XXXXXXX54", "loa_claim": DigiDAssuranceLevels.middle},
        )


class ProcessClaimsDigiDMachtigenTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.plugin = registry[OIDC_DIGID_MACHTIGEN_IDENTIFIER]

    @mock_oidc_client(
        OIDC_DIGID_MACHTIGEN_IDENTIFIER,
        overrides={
            "options.identity_settings.representee_bsn_claim_path": ["representee"],
            "options.identity_settings.authorizee_bsn_claim_path": ["authorizee"],
            "options.identity_settings.mandate_service_id_claim_path": ["service_id"],
            "options.loa_settings": {
                "claim_path": ["authsp_level"],
                "default": DigiDAssuranceLevels.middle,
                "value_mapping": [
                    {"from": "30", "to": DigiDAssuranceLevels.high},
                ],
            },
        },
    )
    def test_process_claims(self):
        with self.subTest("BSN extraction + transform loa values"):
            processed_claims = process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authorizee": "XXXXXXX99",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                    "extra": "irrelevant",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "representee_bsn_claim": "XXXXXXX54",
                    "authorizee_bsn_claim": "XXXXXXX99",
                    "loa_claim": DigiDAssuranceLevels.high,
                    "mandate_service_id_claim": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
            )

        with self.subTest("BSN extraction + missing loa claim"):
            processed_claims = process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authorizee": "XXXXXXX99",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "representee_bsn_claim": "XXXXXXX54",
                    "authorizee_bsn_claim": "XXXXXXX99",
                    "loa_claim": DigiDAssuranceLevels.middle,
                    "mandate_service_id_claim": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
            )

        with self.subTest("BSN extraction + unmapped LOA value"):
            processed_claims = process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authorizee": "XXXXXXX99",
                    "authsp_level": "20",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                    "extra": "irrelevant",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "representee_bsn_claim": "XXXXXXX54",
                    "authorizee_bsn_claim": "XXXXXXX99",
                    "loa_claim": "20",
                    "mandate_service_id_claim": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
            )

    @mock_oidc_client(
        OIDC_DIGID_MACHTIGEN_IDENTIFIER,
        overrides={
            "options.identity_settings.representee_bsn_claim_path": ["representee"],
            "options.identity_settings.authorizee_bsn_claim_path": ["authorizee"],
            "options.identity_settings.mandate_service_id_claim_path": ["service_id"],
            "options.loa_settings.claim_path": ["authsp_level"],
        },
    )
    def test_digid_machtigen_raises_on_missing_claims(self):
        with self.assertRaises(ValueError):
            process_claims(
                {},
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "authorizee": "XXXXXXX99",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authorizee": "XXXXXXX99",
                    "authsp_level": "30",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

    @mock_oidc_client(
        OIDC_DIGID_MACHTIGEN_IDENTIFIER,
        overrides={
            "options.identity_settings.representee_bsn_claim_path": ["representee"],
            "options.identity_settings.authorizee_bsn_claim_path": ["authorizee"],
            "options.identity_settings.mandate_service_id_claim_path": ["service_id"],
            "options.loa_settings.claim_path": ["authsp_level"],
        },
    )
    def test_lax_mode(self):
        with self.assertRaises(ValueError):
            process_claims(
                {},
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "authorizee": "XXXXXXX99",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

        processed_claims = process_claims(
            {
                "representee": "XXXXXXX54",
                "authorizee": "XXXXXXX99",
                "authsp_level": "30",
            },
            self.plugin.get_claim_processing_instructions(),
            strict=False,
        )

        self.assertEqual(
            processed_claims,
            {
                "representee_bsn_claim": "XXXXXXX54",
                "authorizee_bsn_claim": "XXXXXXX99",
                "loa_claim": "30",
            },
        )


class ProcessClaimsEHTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.plugin = registry[OIDC_EH_IDENTIFIER]

    @mock_oidc_client(
        OIDC_EH_IDENTIFIER,
        overrides={
            "options.identity_settings.identifier_type_claim_path": ["namequalifier"],
            "options.identity_settings.legal_subject_claim_path": ["kvk"],
            "options.identity_settings.acting_subject_claim_path": ["sub"],
            "options.identity_settings.branch_number_claim_path": ["vestiging"],
            "options.loa_settings": {
                "claim_path": ["loa"],
                "default": AssuranceLevels.low_plus,
                "value_mapping": [
                    {"from": 3, "to": AssuranceLevels.substantial},
                ],
            },
        },
    )
    def test_process_claims(self):
        with self.subTest("all claims provided, happy flow"):
            processed_claims = process_claims(
                {
                    "namequalifier": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "vestiging": "123456789012",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "extra": "ignored",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "identifier_type_claim": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                    "legal_subject_claim": "12345678",
                    "acting_subject_claim": "-opaquestring-",
                    "branch_number_claim": "123456789012",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

        with self.subTest("all required claims provided, happy flow"):
            processed_claims = process_claims(
                {
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_claim": "12345678",
                    "acting_subject_claim": "-opaquestring-",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

        with self.subTest("mapping loa value"):
            processed_claims = process_claims(
                {
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "loa": 3,
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_claim": "12345678",
                    "acting_subject_claim": "-opaquestring-",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa3",
                },
            )

        with self.subTest("default/fallback loa"):
            processed_claims = process_claims(
                {
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_claim": "12345678",
                    "acting_subject_claim": "-opaquestring-",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

    @mock_oidc_client(
        OIDC_EH_IDENTIFIER,
        overrides={
            "options.identity_settings.identifier_type_claim_path": ["namequalifier"],
            "options.identity_settings.legal_subject_claim_path": ["kvk"],
            "options.identity_settings.acting_subject_claim_path": ["sub"],
            "options.identity_settings.branch_number_claim_path": ["vestiging"],
            "options.loa_settings": {
                "claim_path": ["loa"],
                "default": AssuranceLevels.low_plus,
                "value_mapping": [
                    {"from": 3, "to": AssuranceLevels.substantial},
                ],
            },
        },
    )
    def test_eherkenning_raises_on_missing_claims(self):
        with self.assertRaises(ValueError):
            process_claims(
                {"kvk": "12345678"},
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {"sub": "-opaquestring-"},
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

    @mock_oidc_client(
        OIDC_EH_IDENTIFIER,
        overrides={
            "options.identity_settings.identifier_type_claim_path": ["namequalifier"],
            "options.identity_settings.legal_subject_claim_path": ["kvk"],
            "options.identity_settings.acting_subject_claim_path": ["sub"],
            "options.identity_settings.branch_number_claim_path": ["vestiging"],
            "options.loa_settings": {
                "claim_path": ["loa"],
                "default": AssuranceLevels.low_plus,
                "value_mapping": [
                    {"from": 3, "to": AssuranceLevels.substantial},
                ],
            },
        },
    )
    def test_lax_mode(self):
        with self.assertRaises(ValueError):
            process_claims(
                {"sub": "-opaquestring-"},
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

        processed_claims = process_claims(
            {"kvk": "12345678"},
            self.plugin.get_claim_processing_instructions(),
            strict=False,
        )

        self.assertEqual(
            processed_claims,
            {"legal_subject_claim": "12345678", "loa_claim": AssuranceLevels.low_plus},
        )


class ProcessClaimsEHBewindvoeringTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.plugin = registry[OIDC_EH_BEWINDVOERING_IDENTIFIER]

    @mock_oidc_client(
        OIDC_EH_BEWINDVOERING_IDENTIFIER,
        overrides={
            "options.identity_settings.identifier_type_claim_path": ["namequalifier"],
            "options.identity_settings.legal_subject_claim_path": ["kvk"],
            "options.identity_settings.acting_subject_claim_path": ["sub"],
            "options.identity_settings.branch_number_claim_path": ["vestiging"],
            "options.identity_settings.representee_claim_path": ["bsn"],
            "options.identity_settings.mandate_service_id_claim_path": ["service_id"],
            "options.identity_settings.mandate_service_uuid_claim_path": [
                "service_uuid"
            ],
            "options.loa_settings": {
                "claim_path": ["loa"],
                "default": AssuranceLevels.low_plus,
                "value_mapping": [
                    {"from": 3, "to": AssuranceLevels.substantial},
                ],
            },
        },
    )
    def test_eherkenning_bewindvoering_claim_processing(self):
        with self.subTest("all claims provided, happy flow"):
            processed_claims = process_claims(
                {
                    "namequalifier": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "vestiging": "123456789012",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "bsn": "XXXXXXX54",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "service_uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                    "extra": "ignored",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "identifier_type_claim": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                    "legal_subject_claim": "12345678",
                    "acting_subject_claim": "-opaquestring-",
                    "branch_number_claim": "123456789012",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                    "representee_claim": "XXXXXXX54",
                    "mandate_service_id_claim": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "mandate_service_uuid_claim": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
            )

        with self.subTest("all required claims provided, happy flow"):
            processed_claims = process_claims(
                {
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "bsn": "XXXXXXX54",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "service_uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_claim": "12345678",
                    "acting_subject_claim": "-opaquestring-",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                    "representee_claim": "XXXXXXX54",
                    "mandate_service_id_claim": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "mandate_service_uuid_claim": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
            )

        with self.subTest("mapping loa value"):
            processed_claims = process_claims(
                {
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "loa": 3,
                    "bsn": "XXXXXXX54",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "service_uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_claim": "12345678",
                    "acting_subject_claim": "-opaquestring-",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa3",
                    "representee_claim": "XXXXXXX54",
                    "mandate_service_id_claim": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "mandate_service_uuid_claim": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
            )

        with self.subTest("default/fallback loa"):
            processed_claims = process_claims(
                {
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "bsn": "XXXXXXX54",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "service_uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_claim": "12345678",
                    "acting_subject_claim": "-opaquestring-",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                    "representee_claim": "XXXXXXX54",
                    "mandate_service_id_claim": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "mandate_service_uuid_claim": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
            )

    @mock_oidc_client(
        OIDC_EH_BEWINDVOERING_IDENTIFIER,
        overrides={
            "options.identity_settings.identifier_type_claim_path": ["namequalifier"],
            "options.identity_settings.legal_subject_claim_path": ["kvk"],
            "options.identity_settings.acting_subject_claim_path": ["sub"],
            "options.identity_settings.branch_number_claim_path": ["vestiging"],
            "options.identity_settings.representee_claim_path": ["bsn"],
            "options.identity_settings.mandate_service_id_claim_path": ["service_id"],
            "options.identity_settings.mandate_service_uuid_claim_path": [
                "service_uuid"
            ],
            "options.loa_settings": {
                "claim_path": ["loa"],
                "default": AssuranceLevels.low_plus,
                "value_mapping": [
                    {"from": 3, "to": AssuranceLevels.substantial},
                ],
            },
        },
    )
    def test_raises_on_missing_claims(self):
        with self.assertRaises(ValueError):
            process_claims(
                {
                    "kvk": "12345678",
                    "bsn": "XXXXXXX54",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "service_uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "sub": "-opaquestring-",
                    "bsn": "XXXXXXX54",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "service_uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "service_uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "bsn": "XXXXXXX54",
                    "service_uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "kvk": "12345678",
                    "sub": "-opaquestring-",
                    "bsn": "XXXXXXX54",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                },
                self.plugin.get_claim_processing_instructions(),
                strict=True,
            )

    @mock_oidc_client(
        OIDC_EH_BEWINDVOERING_IDENTIFIER,
        overrides={
            "options.identity_settings.identifier_type_claim_path": ["namequalifier"],
            "options.identity_settings.legal_subject_claim_path": ["kvk"],
            "options.identity_settings.acting_subject_claim_path": ["sub"],
            "options.identity_settings.branch_number_claim_path": ["vestiging"],
            "options.identity_settings.representee_claim_path": ["bsn"],
            "options.identity_settings.mandate_service_id_claim_path": ["service_id"],
            "options.identity_settings.mandate_service_uuid_claim_path": [
                "service_uuid"
            ],
            "options.loa_settings": {
                "claim_path": ["loa"],
                "default": AssuranceLevels.low_plus,
                "value_mapping": [
                    {"from": 3, "to": AssuranceLevels.substantial},
                ],
            },
        },
    )
    def test_lax_mode(self):
        processed_claims = process_claims(
            {
                "kvk": "12345678",
                "bsn": "XXXXXXX54",
            },
            self.plugin.get_claim_processing_instructions(),
            strict=False,
        )

        self.assertEqual(
            processed_claims,
            {
                "legal_subject_claim": "12345678",
                "representee_claim": "XXXXXXX54",
                "loa_claim": AssuranceLevels.low_plus,
            },
        )


class OIDCUtilsTests(TestCase):
    def test_processing_claims(self):
        idp_claims = {
            "bsn": "123456782",
            "user": {"pet": "cat", "some": "other info"},
            "loa": "urn:etoegang:core:assurance-class:loa1",
        }

        config = OIDCClientFactory.create(
            identifier="test-processing-claims-non-legacy",
            enabled=True,
            with_admin_options=True,
            options={
                "bsn_path": ["bsn"],
                "user_info": {
                    "pet_path": ["user", "pet"],
                },
                "other_config": "bla",
                "loa_settings": {"claim_path": ["loa"]},
            },
        )

        processing_instructions: ClaimProcessingInstructions = {
            "always_required_claims": [
                {
                    "path_in_claim": config.options["bsn_path"],
                    "processed_path": ["bsn_claim"],
                }
            ],
            "strict_required_claims": [
                {
                    "path_in_claim": config.options["user_info"]["pet_path"],
                    "processed_path": ["user", "pet"],
                }
            ],
            "optional_claims": [],
            "loa_claims": {
                "default": "",
                "value_mapping": [],
                "path_in_claim": ["loa"],
                "processed_path": ["bla_loa_claim"],
            },
        }

        processed_claims = process_claims(
            idp_claims,
            processing_instructions,
            strict=True,
        )

        expected_claims = {
            "bsn_claim": "123456782",
            "user": {
                "pet": "cat",
            },
            "bla_loa_claim": "urn:etoegang:core:assurance-class:loa1",
        }

        self.assertEqual(expected_claims, processed_claims)
