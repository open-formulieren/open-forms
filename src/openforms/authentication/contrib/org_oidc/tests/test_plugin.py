from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from ..oidc_plugins.constants import OIDC_ORG_IDENTIFIER
from ..plugin import OIDCAuthentication


class OIDCAuthenticationVendorHintTests(SimpleTestCase):
    plugin: OIDCAuthentication

    def setUp(self):
        self.plugin = OIDCAuthentication("org-oidc")

    def test_get_vendor_hint_success(self):
        mock_plugin = MagicMock()
        mock_plugin.get_config.return_value.oidc_provider.oidc_op_authorization_endpoint = "https://oidc.example.com/auth"

        with patch.dict(
            "openforms.authentication.contrib.org_oidc.plugin.oidc_registry._registry",
            {OIDC_ORG_IDENTIFIER: mock_plugin},
        ):
            self.assertEqual(
                self.plugin.get_vendor_hint({}), "https://oidc.example.com/auth"
            )

    def test_get_vendor_hint_plugin_or_config_does_not_exist(self):
        mock_plugin = MagicMock()
        mock_plugin.get_config.side_effect = RuntimeError("Not configured")
        with patch.dict(
            "openforms.authentication.contrib.org_oidc.plugin.oidc_registry._registry",
            {OIDC_ORG_IDENTIFIER: mock_plugin},
        ):
            self.assertIsNone(self.plugin.get_vendor_hint({}))
