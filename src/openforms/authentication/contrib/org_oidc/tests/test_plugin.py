from django.test import TestCase

from mozilla_django_oidc_db.tests.mixins import OIDCMixin

from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory

from ..plugin import OIDCAuthentication


class OIDCAuthenticationVendorHintTests(OIDCMixin, TestCase):
    plugin: OIDCAuthentication

    def setUp(self):
        super().setUp()
        self.plugin = OIDCAuthentication("org-oidc")

    def _get_options(self):
        assert self.plugin.configuration_options is not None
        serializer = self.plugin.configuration_options(data={})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def test_get_vendor_hint_success(self):
        OFOIDCClientFactory.create(
            with_org=True,
            oidc_provider__oidc_op_authorization_endpoint="https://oidc.example.com/auth",
        )

        self.assertEqual(
            self.plugin.get_vendor_hint(self._get_options()),
            "https://oidc.example.com/auth",
        )

    def test_get_vendor_hint_no_endpoint(self):
        OFOIDCClientFactory.create(
            with_org=True,
            oidc_provider__oidc_op_authorization_endpoint="",
        )

        self.assertIsNone(self.plugin.get_vendor_hint(self._get_options()))
