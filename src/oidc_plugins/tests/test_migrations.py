from django.core.management import call_command
from django.db import connections

from mozilla_django_oidc_db.models import UserInformationClaimsSources
from solo.models import DEFAULT_SINGLETON_INSTANCE_ID

from oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_ORG_IDENTIFIER,
)
from openforms.utils.tests.test_migrations import TestMigrations

BASE = "https://mock-oidc-provider:9999"


class OIDCConfigModelMigrationTests(TestMigrations):
    app = "oidc_plugins"
    migrate_from = "0001_initial"
    migrate_to = "0002_move_data_oidc_config"

    def _fixture_teardown(self):
        """Overwrite the parent so that we can use TRUNCATE ... CASCADE

        Table "mozilla_django_oidc_db_openidconnectconfig_default_groups" references "auth_group".
        But truncating a table referenced in a foreign key constraint gives an error, so we use
        TRUNCATE ... CASCADE to truncate the table at teardown.
        """
        # Allow TRUNCATE ... CASCADE and don't emit the post_migrate signal
        # when flushing only a subset of the apps
        for db_name in self._databases_names(include_mirrors=False):
            # Flush the database
            inhibit_post_migrate = (
                self.available_apps is not None
                or (  # Inhibit the post_migrate signal when using serialized
                    # rollback to avoid trying to recreate the serialized data.
                    self.serialized_rollback
                    and hasattr(connections[db_name], "_test_serialized_contents")
                )
            )
            call_command(
                "flush",
                verbosity=0,
                interactive=False,
                database=db_name,
                reset_sequences=False,
                allow_cascade=True,  # OVERRIDE FROM PARENT!
                inhibit_post_migrate=inhibit_post_migrate,
            )

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
        OrgOpenIDConnectConfig = apps.get_model(
            "authentication_org_oidc", "OrgOpenIDConnectConfig"
        )
        Group = apps.get_model("auth", "Group")

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
        config, _ = OrgOpenIDConnectConfig.objects.update_or_create(
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
                "username_claim": ["email"],
                "claim_mapping": {
                    "first_name": ["first_name"],
                    "last_name": ["last_name"],
                    "email": ["email"],
                },
                "groups_claim": ["roles"],
                "sync_groups": True,
                "sync_groups_glob_pattern": "*",
                "make_users_staff": False,
                "superuser_group_names": ["Balloons"],
            },
        )
        group_default, _ = Group.objects.get_or_create(name="Opossum")
        config.default_groups.set([group_default])

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

    def test_migrate_org_configuration_forward(self):
        OIDCClient = self.apps.get_model("mozilla_django_oidc_db", "OIDCClient")

        new_config = OIDCClient.objects.get(identifier=OIDC_ORG_IDENTIFIER)
        self.assertEqual(
            new_config.options["user_settings"]["claim_mappings"],
            {
                "username": ["email"],
                "first_name": ["first_name"],
                "last_name": ["last_name"],
                "email": ["email"],
            },
        )
        self.assertTrue(new_config.options["user_settings"]["username_case_sensitive"])
        self.assertEqual(
            new_config.options["groups_settings"],
            {
                "claim_mapping": ["roles"],
                "sync": True,
                "sync_pattern": "*",
                "default_groups": ["Opossum"],
                "make_users_staff": False,
                "superuser_group_names": ["Balloons"],
            },
        )
