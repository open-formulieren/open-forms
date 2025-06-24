from django.core.exceptions import ValidationError
from django.test import TestCase

from openforms.authentication.contrib.generic_oidc.backends import GenericOIDCBackend
from openforms.authentication.contrib.yivi_oidc.models import YiviOpenIDConnectConfig
from openforms.authentication.contrib.yivi_oidc.tests.base import mock_yivi_config
from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.forms.tests.factories import FormAuthenticationBackendFactory


class ProcessClaimsTest(TestCase):
    """
    Test functionality of the `_process_claims` method of the GenericOIDCBackend class.
    """

    def setUp(self):
        super().setUp()

        self.backend = GenericOIDCBackend()

    @mock_yivi_config(
        bsn_loa_claim=["loa:bsn"],
        bsn_default_loa="",
        kvk_loa_claim=["loa:kvk"],
        kvk_default_loa="",
    )
    def test_process_claims_for_yivi_plugin_without_authentication_claims(self):
        self.backend.config_class = YiviOpenIDConnectConfig
        self.backend._config = YiviOpenIDConnectConfig.get_solo()

        processed_claims = self.backend._process_claims(
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "example@test.com",
                "date_of_birth": "1970-01-01",
            }
        )

        self.assertEqual(processed_claims, {})

    @mock_yivi_config(
        pseudo_claim=["sub"],
        bsn_loa_claim=["loa:bsn"],
        bsn_default_loa="",
        kvk_loa_claim=["loa:kvk"],
        kvk_default_loa="",
    )
    def test_process_claims_for_yivi_plugin_with_pseudo_authentication_claims(self):
        self.backend.config_class = YiviOpenIDConnectConfig
        self.backend._config = YiviOpenIDConnectConfig.get_solo()

        processed_claims = self.backend._process_claims(
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "example@test.com",
                "date_of_birth": "1970-01-01",
                "sub": "hashed-pseudo-id",
            }
        )

        self.assertEqual(processed_claims, {"pseudo_claim": "hashed-pseudo-id"})

    @mock_yivi_config(
        bsn_claim=["bsn"],
        bsn_loa_claim=["loa:bsn"],
        bsn_default_loa="",
        kvk_loa_claim=["loa:kvk"],
        kvk_default_loa="",
    )
    def test_process_claims_for_yivi_plugin_with_authentication_bsn_claims(self):
        self.backend.config_class = YiviOpenIDConnectConfig
        self.backend._config = YiviOpenIDConnectConfig.get_solo()

        processed_claims = self.backend._process_claims(
            {
                "bsn": "123456789",
                "loa:bsn": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                "first_name": "John",
                "last_name": "Doe",
            }
        )

        self.assertEqual(
            processed_claims,
            {
                "bsn_claim": "123456789",
                "loa_claim": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
            },
        )

    @mock_yivi_config(
        bsn_loa_claim=["loa:bsn"],
        bsn_default_loa="",
        identifier_type_claim=["namequalifier"],
        legal_subject_claim=["kvk"],
        acting_subject_claim=["sub"],
        branch_number_claim=["branch"],
        kvk_loa_claim=["loa:kvk"],
        kvk_default_loa="",
    )
    def test_process_claims_for_yivi_plugin_with_authentication_kvk_claims(self):
        self.backend.config_class = YiviOpenIDConnectConfig
        self.backend._config = YiviOpenIDConnectConfig.get_solo()

        processed_claims = self.backend._process_claims(
            {
                "kvk": "12345678",
                "namequalifier": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                "loa:kvk": "urn:etoegang:core:assurance-class:loa2",
                "branch": "123456789012",
                "sub": "hashed-pseudo-id",
                "email": "example@test.com",
            }
        )

        self.assertEqual(
            processed_claims,
            {
                "legal_subject_claim": "12345678",
                "identifier_type_claim": "urn:etoegang:1.9:EntityConcernedID:KvKnr",
                "acting_subject_claim": "hashed-pseudo-id",
                "loa_claim": "urn:etoegang:core:assurance-class:loa2",
                "branch_number_claim": "123456789012",
                "pseudo_claim": "hashed-pseudo-id",
            },
        )


class ExtractAdditionalClaimsForAuthBackendTest(TestCase):
    """
    Test functionality of the `_extract_additional_claims_for_auth_backend` method of the GenericOIDCBackend class.
    """

    def setUp(self):
        super().setUp()

        self.backend = GenericOIDCBackend()

    def test_extracting_additional_claims_for_unknown_auth_backend(self):
        with self.assertRaises(ValidationError) as error:
            self.backend._extract_additional_claims_for_auth_backend("4", {})

        self.assertEqual(error.exception.code, "not_found")

    def test_extracting_additional_claims_for_yivi_auth_backend_without_additional_attributes_groups(
        self,
    ):
        auth_backend = FormAuthenticationBackendFactory(backend="yivi_oidc", options={})
        extracted_claims = self.backend._extract_additional_claims_for_auth_backend(
            auth_backend.id,
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "example@test.com",
                "date_of_birth": "1970-01-01",
            },
        )
        self.assertEqual(extracted_claims, {})

    def test_extracting_additional_claims_for_yivi_auth_backend_with_additional_attributes_groups(
        self,
    ):
        AttributeGroupFactory(name="profile", attributes=["first_name", "last_name"])

        auth_backend = FormAuthenticationBackendFactory(
            backend="yivi_oidc", options={"additional_attributes_groups": ["profile"]}
        )
        extracted_claims = self.backend._extract_additional_claims_for_auth_backend(
            auth_backend.id,
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "example@test.com",
                "date_of_birth": "1970-01-01",
            },
        )

        # Expect that only the attributes defined in the auth backend
        # `additional_attributes_groups` are returned
        self.assertEqual(
            extracted_claims,
            {
                "first_name": "John",
                "last_name": "Doe",
            },
        )
