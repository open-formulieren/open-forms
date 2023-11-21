from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from cookie_consent.models import Cookie

from openforms.config.models import CSPSetting

from ..constants import AnalyticsTools
from .mixin import AnalyticsMixin


@override_settings(SOLO_CACHE=None, BASE_URL="https://example.com:8443/foo")
class MatomoTests(AnalyticsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.matomo_url = "https://example.com"

        cls.json_cookies = [
            {"name": "_pk_id.1234.8809", "path": "/"},
            {"name": "_pk_ses.1234.8809", "path": "/"},
        ]

        cls.json_csp = [{"directive": "default-src", "value": cls.matomo_url}]

    def test_matomo_properly_enabled(self):

        self.config.matomo_url = self.matomo_url
        self.config.matomo_site_id = "1234"

        self.config.enable_matomo_site_analytics = True
        self.config.clean()
        self.config.save()

        for cookie in self.json_cookies:
            with self.subTest(cookie=cookie):
                try:
                    Cookie.objects.get(name=cookie["name"])
                except Cookie.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

        for csp in self.json_csp:
            with self.subTest("Test creation of CSP"):
                try:
                    CSPSetting.objects.get(
                        value=csp["value"],
                        directive=csp["directive"],
                        identifier=AnalyticsTools.matomo,
                    )
                except CSPSetting.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

    def test_matomo_properly_disabled(self):
        self.config.matomo_url = self.matomo_url
        self.config.matomo_site_id = "1234"

        # creation of cookies
        self.config.enable_matomo_site_analytics = True
        self.config.clean()
        self.config.save()

        # Deletion of cookies
        self.config.enable_matomo_site_analytics = False
        self.config.clean()
        self.config.save()

        for cookie in self.json_cookies:
            with self.subTest("Test deletion of cookies"):
                self.assertFalse(Cookie.objects.filter(name=cookie["name"]).exists())

        for csp in self.json_csp:
            with self.subTest("Test deletion of CSP"):
                self.assertFalse(
                    CSPSetting.objects.filter(
                        value=csp["value"],
                        directive=csp["directive"],
                        identifier=AnalyticsTools.matomo,
                    ).exists()
                )

    def test_matomo_enabled_but_related_fields_are_not(self):
        self.config.enable_matomo_site_analytics = True

        with self.assertRaises(ValidationError):
            self.config.clean()
