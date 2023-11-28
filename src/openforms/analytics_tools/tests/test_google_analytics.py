from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from cookie_consent.models import Cookie

from openforms.config.models import CSPSetting

from ..constants import AnalyticsTools
from .mixin import AnalyticsMixin


@override_settings(SOLO_CACHE=None)
class GoogleAnalyticsTests(AnalyticsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.gtm_code = "GTM-XXXX"
        cls.ga_code = "UA-XXXXX-Y"
        cls.json_cookies = [
            {"name": "_ga", "path": "/"},
            {"name": "_gat", "path": "/"},
            {"name": "_gid", "path": "/"},
        ]
        cls.json_csp = [
            {"directive": "default-src", "value": "https://www.googleanalytics.com"},
            {"directive": "default-src", "value": "https://www.googletagmanager.com"},
        ]

    def test_google_analytics_properly_enabled(self):
        self.config.gtm_code = self.ga_code
        self.config.ga_code = self.gtm_code
        self.config.enable_google_analytics = True
        self.config.save()

        for cookie in self.json_cookies:
            with self.subTest("Test creation of cookies"):
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
                        identifier=AnalyticsTools.google_analytics,
                    )
                except CSPSetting.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

    def test_google_analytics_properly_disabled(self):
        self.config.gtm_code = self.ga_code
        self.config.ga_code = self.gtm_code

        # creation of cookies
        self.config.enable_google_analytics = True
        self.config.clean()
        self.config.save()

        # Deletion of cookies
        self.config.enable_google_analytics = False
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
                        identifier=AnalyticsTools.google_analytics,
                    ).exists()
                )

    def test_google_analytics_enabled_but_related_fields_are_not(self):
        self.config.enable_google_analytics = True

        with self.assertRaises(ValidationError):
            self.config.clean()
