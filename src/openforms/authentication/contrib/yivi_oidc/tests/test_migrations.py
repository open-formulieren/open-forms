from digid_eherkenning.choices import AssuranceLevels
from mozilla_django_oidc_db.models import UserInformationClaimsSources
from solo.models import DEFAULT_SINGLETON_INSTANCE_ID

from openforms.utils.tests.test_migrations import TestMigrations, TruncateCascadeMixin

from ..oidc_plugins.constants import OIDC_YIVI_IDENTIFIER

BASE = "https://mock-oidc-provider:9999"


class OIDCConfigModelMigrationTests(TruncateCascadeMixin, TestMigrations):
    app = "yivi_oidc"
    migrate_from = "0001_initial"
    migrate_to = "0002_move_data_oidc"

    def setUpBeforeMigration(self, apps):
        YiviOpenIDConnectConfig = apps.get_model("yivi_oidc", "YiviOpenIDConnectConfig")

        YiviOpenIDConnectConfig.objects.update_or_create(
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
                "oidc_rp_scopes_list": ["openid", "bsn"],
                "loa_claim": ["loa"],
                "default_loa": AssuranceLevels.low_plus,
                "loa_value_mapping": ["loa_value"],
                "bsn_claim": ["bsn"],
                "bsn_loa_claim": ["bsn.loa"],
                "bsn_default_loa": AssuranceLevels.low,
                "bsn_loa_value_mapping": [{"from": "bla", "to": "blo"}],
                "kvk_claim": ["kvk"],
                "kvk_loa_claim": ["kvk.loa"],
                "kvk_default_loa": AssuranceLevels.high,
                "kvk_loa_value_mapping": [{"from": "foo", "to": "bar"}],
                "pseudo_claim": ["pbdf.sidn-pbdf.irma.pseudonym"],
            },
        )

    def test_migrate_configuration_forward(self):
        OIDCClient = self.apps.get_model("mozilla_django_oidc_db", "OIDCClient")

        new_config = OIDCClient.objects.get(identifier=OIDC_YIVI_IDENTIFIER)

        self.assertEqual(
            new_config.oidc_provider.oidc_op_discovery_endpoint, f"{BASE}/oidc/"
        )
        self.assertEqual(
            new_config.oidc_provider.oidc_op_jwks_endpoint, f"{BASE}/oidc/jwks"
        )
        self.assertEqual(
            new_config.oidc_provider.oidc_op_authorization_endpoint,
            f"{BASE}/oidc/auth",
        )
        self.assertEqual(
            new_config.oidc_provider.oidc_op_token_endpoint, f"{BASE}/oidc/token"
        )
        self.assertEqual(
            new_config.oidc_provider.oidc_op_user_endpoint, f"{BASE}/oidc/user"
        )

        self.assertTrue(new_config.enabled)
        self.assertEqual(new_config.oidc_rp_client_id, "fake")
        self.assertEqual(new_config.oidc_rp_client_secret, "even-faker")
        self.assertEqual(new_config.oidc_rp_sign_algo, "RS256")
        self.assertEqual(new_config.oidc_rp_scopes_list, ["openid", "bsn"])
        self.assertEqual(new_config.oidc_rp_idp_sign_key, "")
        self.assertFalse(new_config.oidc_provider.oidc_token_use_basic_auth)
        self.assertTrue(new_config.oidc_provider.oidc_use_nonce)
        self.assertEqual(new_config.oidc_provider.oidc_nonce_size, 32)
        self.assertEqual(new_config.oidc_provider.oidc_state_size, 32)
        self.assertEqual(new_config.oidc_keycloak_idp_hint, "")
        self.assertEqual(
            new_config.userinfo_claims_source,
            UserInformationClaimsSources.userinfo_endpoint,
        )
        self.assertFalse(new_config.check_op_availability)

        self.assertEqual(
            new_config.options["loa_settings"],
            {
                "bsn_loa_claim_path": ["bsn.loa"],
                "bsn_default_loa": AssuranceLevels.low,
                "bsn_loa_value_mapping": [{"from": "bla", "to": "blo"}],
                "kvk_loa_claim_path": ["kvk.loa"],
                "kvk_default_loa": AssuranceLevels.high,
                "kvk_loa_value_mapping": [{"from": "foo", "to": "bar"}],
            },
        )

        self.assertEqual(
            new_config.options["identity_settings"],
            {
                "bsn_claim_path": ["bsn"],
                "kvk_claim_path": ["kvk"],
                "pseudo_claim_path": ["pbdf.sidn-pbdf.irma.pseudonym"],
            },
        )


class OIDCConfigModelBackwardMigrationTests(TruncateCascadeMixin, TestMigrations):
    app = "yivi_oidc"
    migrate_from = "0002_move_data_oidc"
    migrate_to = "0001_initial"

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
            identifier=OIDC_YIVI_IDENTIFIER,
            defaults={
                "oidc_provider": provider,
                "enabled": True,
                "oidc_rp_client_id": "fake",
                "oidc_rp_client_secret": "even-faker",
                "oidc_rp_sign_algo": "RS256",
                "oidc_rp_scopes_list": ["openid", "bsn"],
                "options": {
                    "loa_settings": {
                        "bsn_loa_claim_path": ["bsn.loa"],
                        "bsn_default_loa": AssuranceLevels.low,
                        "bsn_loa_value_mapping": [{"from": "bla", "to": "blo"}],
                        "kvk_loa_claim_path": ["kvk.loa"],
                        "kvk_default_loa": AssuranceLevels.high,
                        "kvk_loa_value_mapping": [{"from": "foo", "to": "bar"}],
                    },
                    "identity_settings": {
                        "bsn_claim_path": ["bsn"],
                        "kvk_claim_path": ["kvk"],
                        "pseudo_claim_path": ["pbdf.sidn-pbdf.irma.pseudonym"],
                    },
                },
            },
        )

    def test_migrate_configuration_backward(self):
        YiviOpenIDConnectConfig = self.apps.get_model(
            "yivi_oidc", "YiviOpenIDConnectConfig"
        )

        old_config = YiviOpenIDConnectConfig.objects.get(
            pk=DEFAULT_SINGLETON_INSTANCE_ID
        )

        self.assertEqual(old_config.bsn_claim, ["bsn"])
        self.assertEqual(old_config.bsn_loa_claim, ["bsn.loa"])
        self.assertEqual(old_config.bsn_default_loa, AssuranceLevels.low)
        self.assertEqual(
            old_config.bsn_loa_value_mapping, [{"from": "bla", "to": "blo"}]
        )
        self.assertEqual(old_config.kvk_claim, ["kvk"])
        self.assertEqual(old_config.kvk_loa_claim, ["kvk.loa"])
        self.assertEqual(old_config.kvk_default_loa, AssuranceLevels.high)
        self.assertEqual(
            old_config.kvk_loa_value_mapping, [{"from": "foo", "to": "bar"}]
        )
        self.assertEqual(old_config.pseudo_claim, ["pbdf.sidn-pbdf.irma.pseudonym"])
