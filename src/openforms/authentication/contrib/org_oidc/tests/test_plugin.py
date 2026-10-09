from unittest.mock import patch

from django.test import SimpleTestCase

from mozilla_django_oidc_db.models import OIDCProvider

from ..plugin import OIDCAuthentication


class OIDCAuthenticationVendorHintTests(SimpleTestCase):
    def setUp(self):
        self.plugin = OIDCAuthentication("org-oidc")

    @patch("openforms.authentication.contrib.org_oidc.plugin.OIDCProvider.objects.get")
    def test_get_vendor_hint_success(self, mock_get):
        mock_get.return_value.authorization_endpoint = "https://oidc.example.com/auth"

        self.assertEqual(
            self.plugin.get_vendor_hint({}), "https://oidc.example.com/auth"
        )
        mock_get.assert_called_once_with(identifier=self.plugin.oidc_plugin_identifier)

    @patch("openforms.authentication.contrib.org_oidc.plugin.OIDCProvider.objects.get")
    def test_get_vendor_hint_provider_does_not_exist(self, mock_get):
        mock_get.side_effect = OIDCProvider.DoesNotExist

        self.assertIsNone(self.plugin.get_vendor_hint({}))
