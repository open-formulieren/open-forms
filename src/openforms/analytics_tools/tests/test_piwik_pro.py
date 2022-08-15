import uuid

from django.core.exceptions import ValidationError

from cookie_consent.models import Cookie

from openforms.config.models import CSPSetting

from .mixin import AnalyticsToolsMixinTestCase


class PiwikProTests(AnalyticsToolsMixinTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.piwik_pro_url = "https://example.com"
        cls.piwik_pro_site_id = uuid.uuid4()
        cls.json_cookies = [
            {"name": f"_pk_id.{cls.piwik_pro_site_id}.e5c3", "path": "/"},
            {"name": f"_pk_ses.{cls.piwik_pro_site_id}.e5c3", "path": "/"},
        ]

        cls.json_csp = [
            {"directive": "script-src", "value": cls.piwik_pro_url},
            {"directive": "connect-src", "value": cls.piwik_pro_url},
            {"directive": "img-src", "value": cls.piwik_pro_url},
            {"directive": "font-src", "value": cls.piwik_pro_url},
            {"directive": "style-src", "value": cls.piwik_pro_url},
        ]

    def test_piwik_pro_properly_enabled(self):
        self.config.piwik_pro_url = self.piwik_pro_url
        self.config.piwik_pro_site_id = self.piwik_pro_site_id

        self.config.enable_piwik_pro_site_analytics = True
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

    def test_piwik_pro_properly_disabled(self):
        self.config.piwik_pro_url = self.piwik_pro_url
        self.config.piwik_pro_site_id = self.piwik_pro_site_id

        # creation of cookies
        self.config.enable_piwik_pro_site_analytics = True
        self.config.clean()
        self.config.save()

        # Deletion of cookies
        self.config.enable_piwik_pro_site_analytics = False
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

    def test_piwik_pro_enabled_but_related_fields_are_not(self):
        self.config.enable_piwik_pro_site_analytics = True

        with self.assertRaises(ValidationError):
            self.config.clean()
