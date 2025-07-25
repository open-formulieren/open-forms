from django.test import TestCase, override_settings
from django.urls import reverse

from mozilla_django_oidc_db.registry import register as registry

from ..oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_DIGID_MACHTIGEN_IDENTIFIER,
    OIDC_EH_BEWINDVOERING_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_EIDAS_COMPANY_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
)


class CallbackURLConfigurationTests(TestCase):
    """
    Test the legacy and new behaviour for the OIDC Redirect URIs for each config.
    """

    @override_settings(USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS=True)
    def test_legacy_settings(self):
        cases = (
            (OIDC_DIGID_IDENTIFIER, "/digid-oidc/callback/"),
            (OIDC_EH_IDENTIFIER, "/eherkenning-oidc/callback/"),
            (OIDC_DIGID_MACHTIGEN_IDENTIFIER, "/digid-machtigen-oidc/callback/"),
            (
                OIDC_EH_BEWINDVOERING_IDENTIFIER,
                "/eherkenning-bewindvoering-oidc/callback/",
            ),
        )

        for identifier, expected_url in cases:
            with self.subTest(
                oidc_plugin_identifier=identifier, expected_url=expected_url
            ):
                plugin = registry[identifier]

                url = reverse(plugin.get_setting("OIDC_AUTHENTICATION_CALLBACK_URL"))

                self.assertEqual(url, expected_url)

    def test_default_settings_behaviour(self):
        cases = (
            OIDC_DIGID_IDENTIFIER,
            OIDC_EH_IDENTIFIER,
            OIDC_DIGID_MACHTIGEN_IDENTIFIER,
            OIDC_EH_BEWINDVOERING_IDENTIFIER,
            OIDC_EIDAS_COMPANY_IDENTIFIER,
            OIDC_EIDAS_IDENTIFIER,
        )

        for identifier in cases:
            with self.subTest(oidc_client_identifier=identifier):
                plugin = registry[identifier]

                url = reverse(plugin.get_setting("OIDC_AUTHENTICATION_CALLBACK_URL"))

                self.assertEqual(url, "/auth/oidc/callback/")
