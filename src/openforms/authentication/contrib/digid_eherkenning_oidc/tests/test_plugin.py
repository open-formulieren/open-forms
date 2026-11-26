from django.test import TestCase

from mozilla_django_oidc_db.tests.mixins import OIDCMixin

from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory

from ....registry import register


class OIDCAuthenticationVendorHintTests(OIDCMixin, TestCase):
    def test_digid(self):
        OFOIDCClientFactory.create(
            with_digid=True,
            oidc_provider__oidc_op_authorization_endpoint="https://oidc.example.com/auth",
        )

        plugin = register["digid_oidc"]
        self.assertEqual(plugin.get_vendor_hint({}), "https://oidc.example.com/auth")

    def test_digid_without_endpoint(self):
        OFOIDCClientFactory.create(
            with_digid=True,
            oidc_provider__oidc_op_authorization_endpoint="",
        )

        plugin = register["digid_oidc"]
        self.assertIsNone(plugin.get_vendor_hint({}))

    def test_digid_without_oidc_provider(self):
        OFOIDCClientFactory.create(with_digid=True, oidc_provider=None)

        plugin = register["digid_oidc"]
        self.assertIsNone(plugin.get_vendor_hint({}))
