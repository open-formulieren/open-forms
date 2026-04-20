from django.test import TestCase
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
    Test behaviour for the OIDC Redirect URIs for each config.
    """

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
