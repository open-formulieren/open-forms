from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from mozilla_django_oidc_db.models import UserInformationClaimsSources
from solo.models import DEFAULT_SINGLETON_INSTANCE_ID

from openforms.utils.tests.test_migrations import TestMigrations, TruncateCascadeMixin

from ...oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
)

BASE = "https://mock-oidc-provider:9999"


class OIDCConfigModelMigrationTests(TruncateCascadeMixin, TestMigrations):
    app = "digid_eherkenning_oidc"
    migrate_from = "0001_initial"
    migrate_to = "0002_move_data_oidc_config"

    def setUpBeforeMigration(self, apps):
        OFDigiDConfig = apps.get_model("digid_eherkenning_oidc", "OFDigiDConfig")
        OFDigiDMachtigenConfig = apps.get_model(
            "digid_eherkenning_oidc", "OFDigiDMachtigenConfig"
        )
        OFEHerkenningConfig = apps.get_model(
            "digid_eherkenning_oidc", "OFEHerkenningConfig"
        )
        OFEHerkenningBewindvoeringConfig = apps.get_model(
            "digid_eherkenning_oidc", "OFEHerkenningBewindvoeringConfig"
        )

        OFDigiDConfig.objects.update_or_create(
            pk=DEFAULT_SINGLETON_INSTANCE_ID,
            defaults={
                "enabled": True,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_op_discovery_endpoint": f"{BASE}/oidc/",
                "oidc_op_jwks_endpoint": f"{BASE}/oidc/jwks",
                "oidc_op_authorization_endpoint": f"{BASE}/oidc/auth",
                "oidc_op_token_endpoint": f"{BASE}/oidc/token",
                "oidc_op_user_endpoint": f"{BASE}/oidc/user",
                "loa_claim": ["loa"],
                "default_loa": "urn:etoegang:core:assurance-class:loa3",
                "loa_value_mapping": ["loa_value"],
                "bsn_claim": ["bsn"],
            },
        )
        OFDigiDMachtigenConfig.objects.update_or_create(
            pk=DEFAULT_SINGLETON_INSTANCE_ID,
            defaults={
                "enabled": True,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_op_discovery_endpoint": f"{BASE}/oidc/",
                "oidc_op_jwks_endpoint": f"{BASE}/oidc/jwks",
                "oidc_op_authorization_endpoint": f"{BASE}/oidc/auth",
                "oidc_op_token_endpoint": f"{BASE}/oidc/token",
                "oidc_op_user_endpoint": f"{BASE}/oidc/user",
                "loa_claim": ["loa"],
                "default_loa": "urn:etoegang:core:assurance-class:loa3",
                "loa_value_mapping": ["loa_value"],
                "representee_bsn_claim": ["representee_bsn"],
                "authorizee_bsn_claim": ["authorizee_bsn"],
                "mandate_service_id_claim": ["mandate"],
            },
        )
        OFEHerkenningConfig.objects.update_or_create(
            pk=DEFAULT_SINGLETON_INSTANCE_ID,
            defaults={
                "enabled": True,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_op_discovery_endpoint": f"{BASE}/oidc/",
                "oidc_op_jwks_endpoint": f"{BASE}/oidc/jwks",
                "oidc_op_authorization_endpoint": f"{BASE}/oidc/auth",
                "oidc_op_token_endpoint": f"{BASE}/oidc/token",
                "oidc_op_user_endpoint": f"{BASE}/oidc/user",
                "loa_claim": ["loa"],
                "default_loa": "urn:etoegang:core:assurance-class:loa3",
                "loa_value_mapping": ["loa_value"],
                "identifier_type_claim": ["identifier_type"],
                "legal_subject_claim": ["legal_subject"],
                "acting_subject_claim": ["acting_subject"],
                "branch_number_claim": ["branch_number"],
            },
        )
        OFEHerkenningBewindvoeringConfig.objects.update_or_create(
            pk=DEFAULT_SINGLETON_INSTANCE_ID,
            defaults={
                "enabled": True,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_op_discovery_endpoint": f"{BASE}/oidc/",
                "oidc_op_jwks_endpoint": f"{BASE}/oidc/jwks",
                "oidc_op_authorization_endpoint": f"{BASE}/oidc/auth",
                "oidc_op_token_endpoint": f"{BASE}/oidc/token",
                "oidc_op_user_endpoint": f"{BASE}/oidc/user",
                "loa_claim": ["loa"],
                "default_loa": "urn:etoegang:core:assurance-class:loa3",
                "loa_value_mapping": ["loa_value"],
                "identifier_type_claim": ["identifier_type"],
                "legal_subject_claim": ["legal_subject"],
                "acting_subject_claim": ["acting_subject"],
                "branch_number_claim": ["branch_number"],
                "representee_claim": ["representee_claim"],
                "mandate_service_id_claim": ["mandate_service_id"],
                "mandate_service_uuid_claim": ["mandate_service_uuid"],
            },
        )

    def test_migrate_digid_configuration_forward(self):
        OIDCClient = self.apps.get_model("mozilla_django_oidc_db", "OIDCClient")

        new_digid_config = OIDCClient.objects.get(identifier=OIDC_DIGID_IDENTIFIER)

        self.assertEqual(
            new_digid_config.oidc_provider.oidc_op_discovery_endpoint, f"{BASE}/oidc/"
        )
        self.assertEqual(
            new_digid_config.oidc_provider.oidc_op_jwks_endpoint, f"{BASE}/oidc/jwks"
        )
        self.assertEqual(
            new_digid_config.oidc_provider.oidc_op_authorization_endpoint,
            f"{BASE}/oidc/auth",
        )
        self.assertEqual(
            new_digid_config.oidc_provider.oidc_op_token_endpoint, f"{BASE}/oidc/token"
        )
        self.assertEqual(
            new_digid_config.oidc_provider.oidc_op_user_endpoint, f"{BASE}/oidc/user"
        )

        self.assertTrue(new_digid_config.enabled)
        self.assertEqual(new_digid_config.oidc_rp_client_id, "fake")
        self.assertEqual(new_digid_config.oidc_rp_client_secret, "even-faker")
        self.assertEqual(new_digid_config.oidc_rp_sign_algo, "RS256")
        self.assertEqual(new_digid_config.oidc_rp_scopes_list, ["openid", "bsn"])
        self.assertEqual(new_digid_config.oidc_rp_idp_sign_key, "")
        self.assertFalse(new_digid_config.oidc_provider.oidc_token_use_basic_auth)
        self.assertTrue(new_digid_config.oidc_provider.oidc_use_nonce)
        self.assertEqual(new_digid_config.oidc_provider.oidc_nonce_size, 32)
        self.assertEqual(new_digid_config.oidc_provider.oidc_state_size, 32)
        self.assertEqual(new_digid_config.oidc_keycloak_idp_hint, "")
        self.assertEqual(
            new_digid_config.userinfo_claims_source,
            UserInformationClaimsSources.userinfo_endpoint,
        )
        self.assertFalse(new_digid_config.check_op_availability)

        self.assertEqual(
            new_digid_config.options["loa_settings"],
            {
                "claim_path": ["loa"],
                "default": "urn:etoegang:core:assurance-class:loa3",
                "value_mapping": ["loa_value"],
            },
        )

        self.assertEqual(
            new_digid_config.options["identity_settings"],
            {
                "bsn_claim_path": ["bsn"],
            },
        )

    def test_migrate_digid_machtigen_configuration_forward(self):
        OIDCClient = self.apps.get_model("mozilla_django_oidc_db", "OIDCClient")

        new_config = OIDCClient.objects.get(identifier=OIDC_DIGID_MACHTIGEN_IDENTIFIER)

        self.assertEqual(
            new_config.options["identity_settings"],
            {
                "representee_bsn_claim_path": ["representee_bsn"],
                "authorizee_bsn_claim_path": ["authorizee_bsn"],
                "mandate_service_id_claim_path": ["mandate"],
            },
        )

    def test_migrate_eherkenning_configuration_forward(self):
        OIDCClient = self.apps.get_model("mozilla_django_oidc_db", "OIDCClient")

        new_config = OIDCClient.objects.get(identifier=OIDC_EH_IDENTIFIER)

        self.assertEqual(
            new_config.options["identity_settings"],
            {
                "identifier_type_claim_path": ["identifier_type"],
                "legal_subject_claim_path": ["legal_subject"],
                "acting_subject_claim_path": ["acting_subject"],
                "branch_number_claim_path": ["branch_number"],
            },
        )

    def test_migrate_eherkenning_bewindvoering_configuration_forward(self):
        OIDCClient = self.apps.get_model("mozilla_django_oidc_db", "OIDCClient")

        new_config = OIDCClient.objects.get(identifier=OIDC_EH_BEWINDVOERING_IDENTIFIER)
        self.assertEqual(
            new_config.options["identity_settings"],
            {
                "identifier_type_claim_path": ["identifier_type"],
                "legal_subject_claim_path": ["legal_subject"],
                "acting_subject_claim_path": ["acting_subject"],
                "branch_number_claim_path": ["branch_number"],
                "representee_claim_path": ["representee_claim"],
                "mandate_service_id_claim_path": ["mandate_service_id"],
                "mandate_service_uuid_claim_path": ["mandate_service_uuid"],
            },
        )


class OIDCConfigModelBackwardMigrationTests(TruncateCascadeMixin, TestMigrations):
    app = "digid_eherkenning_oidc"
    migrate_to = "0001_initial"
    migrate_from = "0002_move_data_oidc_config"

    def _go_to_migration(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(
            [
                ("digid_eherkenning_oidc", "0001_initial"),
            ]
        )

        # If only using ("digid_eherkenning_oidc", "0001_initial"), the other apps are not at the right state
        self.apps = executor.loader.project_state(
            [
                (
                    "mozilla_django_oidc_db",
                    "0006_oidcprovider_oidcclient",
                ),
                ("digid_eherkenning_oidc", "0001_initial"),
                (
                    "digid_eherkenning_oidc_generics",
                    "0009_remove_digidconfig_oidc_exempt_urls_and_more",
                ),
            ]
        ).apps

    def setUpBeforeMigration(self, apps):
        OIDCClient = apps.get_model("mozilla_django_oidc_db", "OIDCClient")
        OIDCProvider = apps.get_model("mozilla_django_oidc_db", "OIDCProvider")

        provider, _ = OIDCProvider.objects.update_or_create(
            identifier="test-provider-migrations",
            defaults={
                "oidc_op_discovery_endpoint": f"{BASE}/oidc/",
                "oidc_op_jwks_endpoint": f"{BASE}/oidc/jwks",
                "oidc_op_authorization_endpoint": f"{BASE}/oidc/auth",
                "oidc_op_token_endpoint": f"{BASE}/oidc/token",
                "oidc_op_user_endpoint": f"{BASE}/oidc/user",
            },
        )

        OIDCClient.objects.update_or_create(
            identifier=OIDC_DIGID_IDENTIFIER,
            defaults={
                "oidc_provider": provider,
                "enabled": True,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_rp_scopes_list": ["openid", "bsn"],
                "options": {
                    "loa_settings": {
                        "claim_path": ["loa"],
                        "default": "urn:etoegang:core:assurance-class:loa3",
                        "value_mapping": ["loa_value"],
                    },
                    "identity_settings": {
                        "bsn_claim_path": ["bsn"],
                    },
                },
            },
        )
        OIDCClient.objects.update_or_create(
            identifier=OIDC_DIGID_MACHTIGEN_IDENTIFIER,
            defaults={
                "oidc_provider": provider,
                "enabled": True,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_rp_scopes_list": ["openid", "bsn"],
                "options": {
                    "loa_settings": {
                        "claim_path": ["loa"],
                        "default": "urn:etoegang:core:assurance-class:loa3",
                        "value_mapping": ["loa_value"],
                    },
                    "identity_settings": {
                        "representee_bsn_claim_path": ["representee_bsn"],
                        "authorizee_bsn_claim_path": ["authorizee_bsn"],
                        "mandate_service_id_claim_path": ["mandate"],
                    },
                },
            },
        )
        OIDCClient.objects.update_or_create(
            identifier=OIDC_EH_IDENTIFIER,
            defaults={
                "oidc_provider": provider,
                "enabled": True,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_rp_scopes_list": ["openid", "kvk"],
                "options": {
                    "loa_settings": {
                        "claim_path": ["loa"],
                        "default": "urn:etoegang:core:assurance-class:loa3",
                        "value_mapping": ["loa_value"],
                    },
                    "identity_settings": {
                        "identifier_type_claim_path": ["identifier_type"],
                        "legal_subject_claim_path": ["legal_subject"],
                        "acting_subject_claim_path": ["acting_subject"],
                        "branch_number_claim_path": ["branch_number"],
                    },
                },
            },
        )
        OIDCClient.objects.update_or_create(
            identifier=OIDC_EH_BEWINDVOERING_IDENTIFIER,
            defaults={
                "oidc_provider": provider,
                "enabled": True,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_rp_scopes_list": ["openid", "kvk"],
                "options": {
                    "loa_settings": {
                        "claim_path": ["loa"],
                        "default": "urn:etoegang:core:assurance-class:loa3",
                        "value_mapping": ["loa_value"],
                    },
                    "identity_settings": {
                        "identifier_type_claim_path": ["identifier_type"],
                        "legal_subject_claim_path": ["legal_subject"],
                        "acting_subject_claim_path": ["acting_subject"],
                        "representee_claim_path": ["representee_claim"],
                        "branch_number_claim_path": ["branch_number"],
                        "mandate_service_id_claim_path": ["mandate_service_id"],
                        "mandate_service_uuid_claim_path": ["mandate_service_uuid"],
                    },
                },
            },
        )

    def test_migrate_digid_configuration_backward(self):
        OFDigiDConfig = self.apps.get_model("digid_eherkenning_oidc", "OFDigiDConfig")

        old_digid_config = OFDigiDConfig.objects.get(pk=DEFAULT_SINGLETON_INSTANCE_ID)

        self.assertEqual(old_digid_config.oidc_op_discovery_endpoint, f"{BASE}/oidc/")
        self.assertEqual(old_digid_config.oidc_op_jwks_endpoint, f"{BASE}/oidc/jwks")
        self.assertEqual(
            old_digid_config.oidc_op_authorization_endpoint,
            f"{BASE}/oidc/auth",
        )
        self.assertEqual(old_digid_config.oidc_op_token_endpoint, f"{BASE}/oidc/token")
        self.assertEqual(old_digid_config.oidc_op_user_endpoint, f"{BASE}/oidc/user")

        self.assertTrue(old_digid_config.enabled)
        self.assertEqual(old_digid_config.oidc_rp_client_id, "fake")
        self.assertEqual(old_digid_config.oidc_rp_client_secret, "even-faker")
        self.assertEqual(old_digid_config.oidc_rp_sign_algo, "RS256")
        self.assertEqual(old_digid_config.oidc_rp_scopes_list, ["openid", "bsn"])
        self.assertEqual(old_digid_config.oidc_rp_idp_sign_key, "")
        self.assertFalse(old_digid_config.oidc_token_use_basic_auth)
        self.assertTrue(old_digid_config.oidc_use_nonce)
        self.assertEqual(old_digid_config.oidc_nonce_size, 32)
        self.assertEqual(old_digid_config.oidc_state_size, 32)
        self.assertEqual(old_digid_config.oidc_keycloak_idp_hint, "")
        self.assertEqual(
            old_digid_config.userinfo_claims_source,
            UserInformationClaimsSources.userinfo_endpoint,
        )
        self.assertEqual(old_digid_config.loa_claim, ["loa"])
        self.assertEqual(
            old_digid_config.default_loa, "urn:etoegang:core:assurance-class:loa3"
        )
        self.assertEqual(old_digid_config.loa_value_mapping, ["loa_value"])
        self.assertEqual(old_digid_config.bsn_claim, ["bsn"])

    def test_migrate_digid_machtigen_configuration_backward(self):
        OFDigiDMachtigenConfig = self.apps.get_model(
            "digid_eherkenning_oidc", "OFDigiDMachtigenConfig"
        )

        old_config = OFDigiDMachtigenConfig.objects.get(
            pk=DEFAULT_SINGLETON_INSTANCE_ID
        )

        self.assertEqual(old_config.representee_bsn_claim, ["representee_bsn"])
        self.assertEqual(old_config.authorizee_bsn_claim, ["authorizee_bsn"])
        self.assertEqual(old_config.mandate_service_id_claim, ["mandate"])

    def test_migrate_eherkenning_configuration_backward(self):
        OFEHerkenningConfig = self.apps.get_model(
            "digid_eherkenning_oidc", "OFEHerkenningConfig"
        )

        old_config = OFEHerkenningConfig.objects.get(pk=DEFAULT_SINGLETON_INSTANCE_ID)

        self.assertEqual(old_config.identifier_type_claim, ["identifier_type"])
        self.assertEqual(old_config.legal_subject_claim, ["legal_subject"])
        self.assertEqual(old_config.acting_subject_claim, ["acting_subject"])
        self.assertEqual(old_config.branch_number_claim, ["branch_number"])

    def test_migrate_eherkenning_bewindvoering_configuration_backward(self):
        OFEHerkenningBewindvoeringConfig = self.apps.get_model(
            "digid_eherkenning_oidc", "OFEHerkenningBewindvoeringConfig"
        )

        old_config = OFEHerkenningBewindvoeringConfig.objects.get(
            pk=DEFAULT_SINGLETON_INSTANCE_ID
        )

        self.assertEqual(old_config.identifier_type_claim, ["identifier_type"])
        self.assertEqual(old_config.legal_subject_claim, ["legal_subject"])
        self.assertEqual(old_config.acting_subject_claim, ["acting_subject"])
        self.assertEqual(old_config.branch_number_claim, ["branch_number"])
        self.assertEqual(old_config.representee_claim, ["representee_claim"])
        self.assertEqual(old_config.mandate_service_id_claim, ["mandate_service_id"])
        self.assertEqual(
            old_config.mandate_service_uuid_claim, ["mandate_service_uuid"]
        )
