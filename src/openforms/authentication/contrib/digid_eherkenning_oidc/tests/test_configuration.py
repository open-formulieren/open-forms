from django.test import TestCase, override_settings
from django.urls import reverse

from mozilla_django_oidc_db.views import OIDCInit

from ..models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
    OFEIDASCompanyConfig,
    OFEIDASConfig,
)


class CallbackURLConfigurationTests(TestCase):
    """
    Test the legacy and new behaviour for the OIDC Redirect URIs for each config.
    """

    def setUp(self):
        super().setUp()

        self.addCleanup(OFDigiDConfig.clear_cache)
        self.addCleanup(OFEHerkenningConfig.clear_cache)
        self.addCleanup(OFDigiDMachtigenConfig.clear_cache)
        self.addCleanup(OFEHerkenningBewindvoeringConfig.clear_cache)
        self.addCleanup(OFEIDASConfig.clear_cache)

    @override_settings(USE_LEGACY_DIGID_EH_OIDC_ENDPOINTS=True)
    def test_legacy_settings(self):
        cases = (
            (OFDigiDConfig, "/digid-oidc/callback/"),
            (OFEHerkenningConfig, "/eherkenning-oidc/callback/"),
            (OFDigiDMachtigenConfig, "/digid-machtigen-oidc/callback/"),
            (
                OFEHerkenningBewindvoeringConfig,
                "/eherkenning-bewindvoering-oidc/callback/",
            ),
        )

        for config_cls, expected_url in cases:
            with self.subTest(config_cls=config_cls, expected_url=expected_url):
                # use an init view to decouple the implementation details from the
                # desired behaviour.
                view = OIDCInit(config_class=config_cls)

                url = reverse(view.get_settings("OIDC_AUTHENTICATION_CALLBACK_URL"))

                self.assertEqual(url, expected_url)

    def test_default_settings_behaviour(self):
        cases = (
            OFDigiDConfig,
            OFEHerkenningConfig,
            OFDigiDMachtigenConfig,
            OFEHerkenningBewindvoeringConfig,
            OFEIDASConfig,
            OFEIDASCompanyConfig,
        )

        for config_cls in cases:
            with self.subTest(config_cls=config_cls):
                # use an init view to decouple the implementation details from the
                # desired behaviour.
                view = OIDCInit(config_class=config_cls)

                url = reverse(view.get_settings("OIDC_AUTHENTICATION_CALLBACK_URL"))

                self.assertEqual(url, "/auth/oidc/callback/")
