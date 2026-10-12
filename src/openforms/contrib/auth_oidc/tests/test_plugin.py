from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from ..plugin import OIDCAuthentication


class DummyOIDCAuthentication(OIDCAuthentication):
    oidc_plugin_identifier = "dummy-oidc"


class OIDCAuthenticationVendorHintTests(SimpleTestCase):
    def setUp(self):
        self.plugin = DummyOIDCAuthentication("dummy")

    def test_get_vendor_hint_success(self):
        mock_plugin = MagicMock()
        mock_plugin.get_config.return_value.oidc_provider.oidc_op_authorization_endpoint = "https://oidc.example.com/auth"

        with patch.dict(
            "openforms.contrib.auth_oidc.plugin.oidc_registry._registry",
            {"dummy-oidc": mock_plugin},
        ):
            self.assertEqual(
                self.plugin.get_vendor_hint({}), "https://oidc.example.com/auth"
            )

    def test_get_vendor_hint_plugin_or_config_does_not_exist(self):
        mock_plugin = MagicMock()
        mock_plugin.get_config.side_effect = RuntimeError("Not configured")
        with patch.dict(
            "openforms.contrib.auth_oidc.plugin.oidc_registry._registry",
            {"dummy-oidc": mock_plugin},
        ):
            self.assertIsNone(self.plugin.get_vendor_hint({}))
