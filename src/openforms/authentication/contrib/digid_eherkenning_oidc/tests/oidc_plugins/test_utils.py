from django.test import TestCase

from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels
from mozilla_django_oidc_db.registry import register as oidc_register
from mozilla_django_oidc_db.tests.mixins import OIDCMixin

from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.contrib.auth_oidc.typing import ClaimProcessingInstructions
from openforms.contrib.auth_oidc.utils import process_claims
from openforms.typing import JSONObject


class ProcessClaimsDigiDTest(OIDCMixin, TestCase):
    def test_digid_process_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid=True,
            options__identity_settings__bsn_claim_path=["sub"],
            options__loa_settings__claim_path=["authsp_level"],
            options__loa_settings__default=DigiDAssuranceLevels.middle,
            options__loa_settings__value_mapping=[
                {"from": "30", "to": DigiDAssuranceLevels.high},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.subTest("BSN extraction + transform loa values"):
            claims: JSONObject = {
                "sub": "XXXXXXX54",
                "authsp_level": "30",
                "extra": "irrelevant",
            }

            processed_claims = process_claims(
                claims,
                plugin.get_claim_processing_instructions(),
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
            claims: JSONObject = {"sub": "XXXXXXX54"}

            processed_claims = process_claims(
                claims,
                plugin.get_claim_processing_instructions(),
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
            claims: JSONObject = {
                "sub": "XXXXXXX54",
                "authsp_level": "20",
                "extra": "irrelevant",
            }

            processed_claims = process_claims(
                claims,
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "bsn_claim": "XXXXXXX54",
                    "loa_claim": "20",
                },
            )

    def test_digid_raises_on_missing_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid=True,
            options__identity_settings__bsn_claim_path=["sub"],
            options__loa_settings__claim_path=["authsp_level"],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.assertRaises(ValueError):
            process_claims(
                {"bsn": "XXXXXXX54"},
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

    def test_digid_loa_claim_absent_without_default_loa(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid=True,
            options__identity_settings__bsn_claim_path=["sub"],
            options__loa_settings__claim_path=["authsp_level"],
            options__loa_settings__default="",
        )

        plugin = oidc_register[oidc_client.identifier]

        processed_claims = process_claims(
            {"sub": "XXXXXXX54"},
            plugin.get_claim_processing_instructions(),
            strict=False,
        )

        self.assertEqual(processed_claims, {"bsn_claim": "XXXXXXX54"})

    def test_digid_loa_claim_not_configured_but_default_set(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid=True,
            options__identity_settings__bsn_claim_path=["bsn"],
            options__loa_settings__claim_path=["not-present"],
            options__loa_settings__default=DigiDAssuranceLevels.middle,
        )

        plugin = oidc_register[oidc_client.identifier]

        processed_claims = process_claims(
            {"bsn": "XXXXXXX54", "loa": "ignored"},
            plugin.get_claim_processing_instructions(),
            strict=False,
        )

        self.assertEqual(
            processed_claims,
            {"bsn_claim": "XXXXXXX54", "loa_claim": DigiDAssuranceLevels.middle},
        )


class ProcessClaimsDigiDMachtigenTest(OIDCMixin, TestCase):
    def test_process_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            options__identity_settings__representee_bsn_claim_path=["representee"],
            options__identity_settings__authorizee_bsn_claim_path=["authorizee"],
            options__identity_settings__mandate_service_id_claim_path=["service_id"],
            options__loa_settings__claim_path=["authsp_level"],
            options__loa_settings__default=DigiDAssuranceLevels.middle,
            options__loa_settings__value_mapping=[
                {"from": "30", "to": DigiDAssuranceLevels.high},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.subTest("BSN extraction + transform loa values"):
            processed_claims = process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authorizee": "XXXXXXX99",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                    "extra": "irrelevant",
                },
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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

    def test_digid_machtigen_raises_on_missing_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            options__identity_settings__representee_bsn_claim_path=["representee"],
            options__identity_settings__authorizee_bsn_claim_path=["authorizee"],
            options__identity_settings__mandate_service_id_claim_path=["service_id"],
            options__loa_settings__claim_path=["authsp_level"],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.assertRaises(ValueError):
            process_claims(
                {},
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "authorizee": "XXXXXXX99",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authorizee": "XXXXXXX99",
                    "authsp_level": "30",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

    def test_lax_mode(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            options__identity_settings__representee_bsn_claim_path=["representee"],
            options__identity_settings__authorizee_bsn_claim_path=["authorizee"],
            options__identity_settings__mandate_service_id_claim_path=["service_id"],
            options__loa_settings__claim_path=["authsp_level"],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.assertRaises(ValueError):
            process_claims(
                {},
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "authorizee": "XXXXXXX99",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "representee": "XXXXXXX54",
                    "authsp_level": "30",
                    "service_id": "46ddda34-c4db-4a54-997c-351bc9a0aabc",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

        processed_claims = process_claims(
            {
                "representee": "XXXXXXX54",
                "authorizee": "XXXXXXX99",
                "authsp_level": "30",
            },
            plugin.get_claim_processing_instructions(),
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


class ProcessClaimsEHTest(OIDCMixin, TestCase):
    def test_process_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            options__identity_settings__identifier_type_claim_path=["namequalifier"],
            options__identity_settings__legal_subject_claim_path=["kvk"],
            options__identity_settings__acting_subject_claim_path=["sub"],
            options__identity_settings__branch_number_claim_path=["vestiging"],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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

    def test_eherkenning_raises_on_missing_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            options__identity_settings__identifier_type_claim_path=["namequalifier"],
            options__identity_settings__legal_subject_claim_path=["kvk"],
            options__identity_settings__acting_subject_claim_path=["sub"],
            options__identity_settings__branch_number_claim_path=["vestiging"],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.assertRaises(ValueError):
            process_claims(
                {"kvk": "12345678"},
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            process_claims(
                {"sub": "-opaquestring-"},
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

    def test_lax_mode(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            options__identity_settings__identifier_type_claim_path=["namequalifier"],
            options__identity_settings__legal_subject_claim_path=["kvk"],
            options__identity_settings__acting_subject_claim_path=["sub"],
            options__identity_settings__branch_number_claim_path=["vestiging"],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.assertRaises(ValueError):
            process_claims(
                {"sub": "-opaquestring-"},
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

        processed_claims = process_claims(
            {"kvk": "12345678"},
            plugin.get_claim_processing_instructions(),
            strict=False,
        )

        self.assertEqual(
            processed_claims,
            {"legal_subject_claim": "12345678", "loa_claim": AssuranceLevels.low_plus},
        )


class ProcessClaimsEHBewindvoeringTest(OIDCMixin, TestCase):
    def test_eherkenning_bewindvoering_claim_processing(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            options__identity_settings__identifier_type_claim_path=["namequalifier"],
            options__identity_settings__legal_subject_claim_path=["kvk"],
            options__identity_settings__acting_subject_claim_path=["sub"],
            options__identity_settings__branch_number_claim_path=["vestiging"],
            options__identity_settings__representee_claim_path=["bsn"],
            options__identity_settings__mandate_service_id_claim_path=["service_id"],
            options__identity_settings__mandate_service_uuid_claim_path=[
                "service_uuid"
            ],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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

    def test_raises_on_missing_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            options__identity_settings__identifier_type_claim_path=["namequalifier"],
            options__identity_settings__legal_subject_claim_path=["kvk"],
            options__identity_settings__acting_subject_claim_path=["sub"],
            options__identity_settings__branch_number_claim_path=["vestiging"],
            options__identity_settings__representee_claim_path=["bsn"],
            options__identity_settings__mandate_service_id_claim_path=["service_id"],
            options__identity_settings__mandate_service_uuid_claim_path=[
                "service_uuid"
            ],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.assertRaises(ValueError):
            process_claims(
                {
                    "kvk": "12345678",
                    "bsn": "XXXXXXX54",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "service_uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                },
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
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
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

    def test_lax_mode(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            options__identity_settings__identifier_type_claim_path=["namequalifier"],
            options__identity_settings__legal_subject_claim_path=["kvk"],
            options__identity_settings__acting_subject_claim_path=["sub"],
            options__identity_settings__branch_number_claim_path=["vestiging"],
            options__identity_settings__representee_claim_path=["bsn"],
            options__identity_settings__mandate_service_id_claim_path=["service_id"],
            options__identity_settings__mandate_service_uuid_claim_path=[
                "service_uuid"
            ],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        processed_claims = process_claims(
            {
                "kvk": "12345678",
                "bsn": "XXXXXXX54",
            },
            plugin.get_claim_processing_instructions(),
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


class ProcessClaimsEidasTest(OIDCMixin, TestCase):
    def test_eidas_claim_processing(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
            options__identity_settings__legal_subject_bsn_identifier_claim_path=["bsn"],
            options__identity_settings__legal_subject_pseudo_identifier_claim_path=[
                "pseudo_id"
            ],
            options__identity_settings__legal_subject_first_name_claim_path=[
                "first_name"
            ],
            options__identity_settings__legal_subject_family_name_claim_path=[
                "family_name"
            ],
            options__identity_settings__legal_subject_date_of_birth_claim_path=[
                "date_of_birth"
            ],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.subTest("all claims provided, happy flow"):
            processed_claims = process_claims(
                {
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_bsn_identifier_claim": "XXXXXXX54",
                    "legal_subject_pseudo_identifier_claim": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "legal_subject_first_name_claim": "John",
                    "legal_subject_family_name_claim": "Doe",
                    "legal_subject_date_of_birth_claim": "01-01-2000",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

        with self.subTest("all claims except bsn provided, happy flow"):
            processed_claims = process_claims(
                {
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_pseudo_identifier_claim": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "legal_subject_first_name_claim": "John",
                    "legal_subject_family_name_claim": "Doe",
                    "legal_subject_date_of_birth_claim": "01-01-2000",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

        with self.subTest("all claims except pseudo_id provided, happy flow"):
            processed_claims = process_claims(
                {
                    "bsn": "XXXXXXX54",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_bsn_identifier_claim": "XXXXXXX54",
                    "legal_subject_first_name_claim": "John",
                    "legal_subject_family_name_claim": "Doe",
                    "legal_subject_date_of_birth_claim": "01-01-2000",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

        with self.subTest("mapping loa value"):
            processed_claims = process_claims(
                {
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": 3,
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_bsn_identifier_claim": "XXXXXXX54",
                    "legal_subject_pseudo_identifier_claim": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "legal_subject_first_name_claim": "John",
                    "legal_subject_family_name_claim": "Doe",
                    "legal_subject_date_of_birth_claim": "01-01-2000",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa3",
                },
            )

        with self.subTest("default/fallback loa"):
            processed_claims = process_claims(
                {
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_bsn_identifier_claim": "XXXXXXX54",
                    "legal_subject_pseudo_identifier_claim": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "legal_subject_first_name_claim": "John",
                    "legal_subject_family_name_claim": "Doe",
                    "legal_subject_date_of_birth_claim": "01-01-2000",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

    def test_raises_on_missing_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
            options__identity_settings__legal_subject_bsn_identifier_claim_path=["bsn"],
            options__identity_settings__legal_subject_pseudo_identifier_claim_path=[
                "pseudo_id"
            ],
            options__identity_settings__legal_subject_first_name_claim_path=[
                "first_name"
            ],
            options__identity_settings__legal_subject_family_name_claim_path=[
                "family_name"
            ],
            options__identity_settings__legal_subject_date_of_birth_claim_path=[
                "date_of_birth"
            ],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.assertRaises(ValueError):
            # Missing first_name
            process_claims(
                {
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            # Missing family_name
            process_claims(
                {
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            # Missing date_of_birth
            process_claims(
                {
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            # Missing bsn and pseudo_id
            process_claims(
                {
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )


class ProcessClaimsEidasCompanyTest(OIDCMixin, TestCase):
    def test_eidas_company_claim_processing(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
            options__identity_settings__legal_subject_identifier_claim_path=[
                "company_id"
            ],
            options__identity_settings__legal_subject_name_claim_path=["company_name"],
            options__identity_settings__acting_subject_bsn_identifier_claim_path=[
                "bsn"
            ],
            options__identity_settings__acting_subject_pseudo_identifier_claim_path=[
                "pseudo_id"
            ],
            options__identity_settings__acting_subject_first_name_claim_path=[
                "first_name"
            ],
            options__identity_settings__acting_subject_family_name_claim_path=[
                "family_name"
            ],
            options__identity_settings__acting_subject_date_of_birth_claim_path=[
                "date_of_birth"
            ],
            options__identity_settings__mandate_service_id_claim_path=["service_id"],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.subTest("all claims provided, happy flow"):
            processed_claims = process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_identifier_claim": "NL/NTR/123456789",
                    "legal_subject_name_claim": "example company BV",
                    "acting_subject_bsn_identifier_claim": "XXXXXXX54",
                    "acting_subject_pseudo_identifier_claim": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "acting_subject_first_name_claim": "John",
                    "acting_subject_family_name_claim": "Doe",
                    "acting_subject_date_of_birth_claim": "01-01-2000",
                    "mandate_service_id_claim": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

        with self.subTest("all claims except bsn provided, happy flow"):
            processed_claims = process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_identifier_claim": "NL/NTR/123456789",
                    "legal_subject_name_claim": "example company BV",
                    "acting_subject_pseudo_identifier_claim": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "acting_subject_first_name_claim": "John",
                    "acting_subject_family_name_claim": "Doe",
                    "acting_subject_date_of_birth_claim": "01-01-2000",
                    "mandate_service_id_claim": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

        with self.subTest("all claims except pseudo_id provided, happy flow"):
            processed_claims = process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "bsn": "XXXXXXX54",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_identifier_claim": "NL/NTR/123456789",
                    "legal_subject_name_claim": "example company BV",
                    "acting_subject_bsn_identifier_claim": "XXXXXXX54",
                    "acting_subject_first_name_claim": "John",
                    "acting_subject_family_name_claim": "Doe",
                    "acting_subject_date_of_birth_claim": "01-01-2000",
                    "mandate_service_id_claim": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

        with self.subTest("mapping loa value"):
            processed_claims = process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "loa": 3,
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_identifier_claim": "NL/NTR/123456789",
                    "legal_subject_name_claim": "example company BV",
                    "acting_subject_bsn_identifier_claim": "XXXXXXX54",
                    "acting_subject_pseudo_identifier_claim": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "acting_subject_first_name_claim": "John",
                    "acting_subject_family_name_claim": "Doe",
                    "acting_subject_date_of_birth_claim": "01-01-2000",
                    "mandate_service_id_claim": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa3",
                },
            )

        with self.subTest("default/fallback loa"):
            processed_claims = process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                },
                plugin.get_claim_processing_instructions(),
                strict=False,
            )

            self.assertEqual(
                processed_claims,
                {
                    "legal_subject_identifier_claim": "NL/NTR/123456789",
                    "legal_subject_name_claim": "example company BV",
                    "acting_subject_bsn_identifier_claim": "XXXXXXX54",
                    "acting_subject_pseudo_identifier_claim": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "acting_subject_first_name_claim": "John",
                    "acting_subject_family_name_claim": "Doe",
                    "acting_subject_date_of_birth_claim": "01-01-2000",
                    "mandate_service_id_claim": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "loa_claim": "urn:etoegang:core:assurance-class:loa2plus",
                },
            )

    def test_raises_on_missing_claims(self):
        oidc_client = OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
            options__identity_settings__legal_subject_identifier_claim_path=[
                "company_id"
            ],
            options__identity_settings__legal_subject_name_claim_path=["company_name"],
            options__identity_settings__acting_subject_bsn_identifier_claim_path=[
                "bsn"
            ],
            options__identity_settings__acting_subject_pseudo_identifier_claim_path=[
                "pseudo_id"
            ],
            options__identity_settings__acting_subject_first_name_claim_path=[
                "first_name"
            ],
            options__identity_settings__acting_subject_family_name_claim_path=[
                "family_name"
            ],
            options__identity_settings__acting_subject_date_of_birth_claim_path=[
                "date_of_birth"
            ],
            options__identity_settings__mandate_service_id_claim_path=["service_id"],
            options__loa_settings__claim_path=["loa"],
            options__loa_settings__default=AssuranceLevels.low_plus,
            options__loa_settings__value_mapping=[
                {"from": 3, "to": AssuranceLevels.substantial},
            ],
        )

        plugin = oidc_register[oidc_client.identifier]

        with self.assertRaises(ValueError):
            # Missing first_name
            process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            # Missing family_name
            process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            # Missing date_of_birth
            process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            # Missing bsn and pseudo_id
            process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            # Missing company_id
            process_claims(
                {
                    "company_name": "example company BV",
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            # Missing company_name
            process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "service_id": "urn:etoegang:DV:00000001002308836000:services:9113",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )

        with self.assertRaises(ValueError):
            # Missing service_id
            process_claims(
                {
                    "company_id": "NL/NTR/123456789",
                    "company_name": "example company BV",
                    "bsn": "XXXXXXX54",
                    "pseudo_id": "BAhmWbLiP6ykmsq7FSg5IXnMLibwZQmBevc6s408FIR3yYIwveaCrfYBjeDeYTuJ6QD02zlb2WWAyfOt/Y4lvxEzdpgtnzCt5TbKJ4cnd0gL",
                    "first_name": "John",
                    "family_name": "Doe",
                    "date_of_birth": "01-01-2000",
                    "loa": "urn:etoegang:core:assurance-class:loa2plus",
                    "extra": "ignored",
                },
                plugin.get_claim_processing_instructions(),
                strict=True,
            )


class OIDCUtilsTests(TestCase):
    def test_processing_claims(self):
        idp_claims: JSONObject = {
            "bsn": "123456782",
            "user": {"pet": "cat", "some": "other info"},
            "loa": "urn:etoegang:core:assurance-class:loa1",
        }

        processing_instructions: ClaimProcessingInstructions = {
            "always_required_claims": [
                {
                    "path_in_claim": ["bsn"],
                    "processed_path": ["bsn_claim"],
                }
            ],
            "strict_required_claims": [
                {
                    "path_in_claim": ["user", "pet"],
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

        expected_claims: JSONObject = {
            "bsn_claim": "123456782",
            "user": {
                "pet": "cat",
            },
            "bla_loa_claim": "urn:etoegang:core:assurance-class:loa1",
        }

        self.assertEqual(expected_claims, processed_claims)
