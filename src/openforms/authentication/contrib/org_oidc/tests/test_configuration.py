from django.test import TestCase, override_settings
from django.urls import reverse

from mozilla_django_oidc_db.registry import register as registry

from ..oidc_plugins.constants import OIDC_ORG_IDENTIFIER


class CallbackURLConfigurationTests(TestCase):
    """
    Test the legacy and new behaviour for the OIDC Redirect URIs for each config.
    """

    @override_settings(USE_LEGACY_ORG_OIDC_ENDPOINTS=True)
    def test_legacy_settings(self):
        # use an init view to decouple the implementation details from the
        # desired behaviour.
        plugin = registry[OIDC_ORG_IDENTIFIER]

        url = reverse(plugin.get_setting("OIDC_AUTHENTICATION_CALLBACK_URL"))

        self.assertEqual(url, "/org-oidc/callback/")

    def test_default_settings_behaviour(self):
        # use an init view to decouple the implementation details from the
        # desired behaviour.
        plugin = registry[OIDC_ORG_IDENTIFIER]

        url = reverse(plugin.get_setting("OIDC_AUTHENTICATION_CALLBACK_URL"))

        self.assertEqual(url, "/auth/oidc/callback/")
