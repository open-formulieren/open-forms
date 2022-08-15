from django.core.exceptions import ValidationError

from cookie_consent.models import Cookie

from openforms.config.models import CSPSetting

from .mixin import AnalyticsToolsMixinTestCase


class SiteImproveTests(AnalyticsToolsMixinTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.siteimprove_id = 1234
        cls.json_cookies = [
            {"name": "AWSELBCORS", "path": "/"},
            {"name": "nmstat", "path": "/"},
        ]

        cls.json_csp = [
            {"directive": "default-src", "value": "siteimproveanalytics.com"},
            {"directive": "img-src", "value": "*.siteimproveanalytics.io"},
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
                        value=csp["value"], directive=csp["directive"]
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
                        value=csp["value"], directive=csp["directive"]
                    ).exists()
                )

    def test_site_improve_enabled_but_related_fields_are_not(self):
        self.config.enable_siteimprove_analytics = True

        with self.assertRaises(ValidationError):
            self.config.clean()
