from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings, tag

from cookie_consent.models import Cookie

from openforms.config.models import CSPSetting

from ..constants import AnalyticsTools
from .mixin import AnalyticsMixin


@override_settings(SOLO_CACHE=None)
class SiteImproveTests(AnalyticsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.siteimprove_id = 1234
        cls.json_cookies = [
            {"name": "AWSELBCORS", "path": "/"},
            {"name": "nmstat", "path": "/"},
        ]

        cls.json_csp = [
            {"directive": "default-src", "value": "https://siteimproveanalytics.com"},
            {"directive": "script-src", "value": "https://siteimproveanalytics.com"},
            {"directive": "img-src", "value": "https://*.siteimproveanalytics.io"},
        ]

    def test_site_improve_properly_enabled(self):
        self.config.siteimprove_id = self.siteimprove_id
        self.config.enable_siteimprove_analytics = True
        self.config.clean()
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
                        identifier=AnalyticsTools.siteimprove,
                    )
                except CSPSetting.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

    def test_site_improve_properly_disabled(self):
        self.config.siteimprove_id = self.siteimprove_id

        # creation of cookies
        self.config.enable_siteimprove_analytics = True
        self.config.clean()
        self.config.save()

        # Deletion of cookies
        self.config.enable_siteimprove_analytics = False
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
                        identifier=AnalyticsTools.siteimprove,
                    ).exists()
                )

    def test_site_improve_enabled_but_related_fields_are_not(self):
        self.config.enable_siteimprove_analytics = True

        with self.assertRaises(ValidationError):
            self.config.clean()

    @tag("gh-2651")
    @override_settings(BASE_URL="https://forms.example.com:8443")
    def test_correct_domain_recorded(self):
        self.config.siteimprove_id = "irrelevant"
        self.config.enable_siteimprove_analytics = True
        self.config.save()

        a_cookie = Cookie.objects.first()

        self.assertIsNotNone(a_cookie)
        self.assertEqual(a_cookie.domain, "forms.example.com")
