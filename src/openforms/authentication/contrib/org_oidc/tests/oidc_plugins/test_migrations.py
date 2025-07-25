from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from solo.models import DEFAULT_SINGLETON_INSTANCE_ID

from openforms.utils.tests.test_migrations import TestMigrations, TruncateCascadeMixin

from ...oidc_plugins.constants import OIDC_ORG_IDENTIFIER

BASE = "https://mock-oidc-provider:9999"


class OIDCConfigModelMigrationTests(TruncateCascadeMixin, TestMigrations):
    app = "authentication_org_oidc"
    migrate_from = "0001_initial"
    migrate_to = "0002_move_oidc_data"

    def setUpBeforeMigration(self, apps):
        OrgOpenIDConnectConfig = apps.get_model(
            "authentication_org_oidc", "OrgOpenIDConnectConfig"
        )
        Group = apps.get_model("auth", "Group")

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


class OIDCConfigModelBackwardsMigrationTests(TruncateCascadeMixin, TestMigrations):
    app = "authentication_org_oidc"
    migrate_to = "0001_initial"
    migrate_from = "0002_move_oidc_data"

    def _go_to_migration(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(
            [
                ("authentication_org_oidc", "0001_initial"),
            ]
        )

        # If only using ("authentication_org_oidc", "0001_initial"), the other apps are not at the right state
        self.apps = executor.loader.project_state(
            [
                (
                    "mozilla_django_oidc_db",
                    "0006_oidcprovider_oidcclient",
                ),
                ("authentication_org_oidc", "0001_initial"),
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
            identifier=OIDC_ORG_IDENTIFIER,
            defaults={
                "enabled": True,
                "oidc_provider": provider,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_rp_scopes_list": ["profile", "email"],
                "options": {
                    "user_settings": {
                        "claim_mappings": {
                            "username": ["email"],
                            "first_name": ["first_name"],
                            "last_name": ["last_name"],
                            "email": ["email"],
                        },
                        "username_case_sensitive": True,
                    },
                    "groups_settings": {
                        "claim_mapping": ["roles"],
                        "sync": True,
                        "sync_pattern": "*-*",
                        "default_groups": ["Top Hat"],
                        "make_users_staff": False,
                        "superuser_group_names": ["Balloons"],
                    },
                },
            },
        )

    def test_migrate_org_configuration_backwards(self):
        OrgOpenIDConnectConfig = self.apps.get_model(
            "authentication_org_oidc", "OrgOpenIDConnectConfig"
        )

        old_config = OrgOpenIDConnectConfig.objects.get(
            pk=DEFAULT_SINGLETON_INSTANCE_ID
        )

        self.assertTrue(old_config.enabled)
        self.assertEqual(old_config.oidc_rp_client_id, "fake")
        self.assertEqual(old_config.oidc_rp_client_secret, "even-faker")
        self.assertEqual(old_config.oidc_op_discovery_endpoint, f"{BASE}/oidc/")
        self.assertEqual(old_config.username_claim, ["email"])
        self.assertEqual(
            old_config.claim_mapping,
            {
                "first_name": ["first_name"],
                "last_name": ["last_name"],
                "email": ["email"],
            },
        )
        self.assertEqual(old_config.groups_claim, ["roles"])
        self.assertTrue(old_config.sync_groups)
        self.assertEqual(old_config.sync_groups_glob_pattern, "*-*")
        self.assertFalse(old_config.make_users_staff)
        self.assertEqual(old_config.superuser_group_names, ["Balloons"])
        self.assertEqual(
            [group.name for group in old_config.default_groups.all()], ["Top Hat"]
        )
