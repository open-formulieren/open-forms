from django.test import TestCase
from django.urls import reverse

from mozilla_django_oidc_db.registry import register as registry

from ..oidc_plugins.constants import OIDC_ORG_IDENTIFIER


class CallbackURLConfigurationTests(TestCase):
    """
    Test behaviour for the OIDC Redirect URIs for each config.
    """

    def test_default_settings_behaviour(self):
        # use an init view to decouple the implementation details from the
        # desired behaviour.
        plugin = registry[OIDC_ORG_IDENTIFIER]

        url = reverse(plugin.get_setting("OIDC_AUTHENTICATION_CALLBACK_URL"))

        self.assertEqual(url, "/auth/oidc/callback/")
