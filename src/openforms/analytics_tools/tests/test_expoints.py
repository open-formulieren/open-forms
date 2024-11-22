from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from openforms.config.models import CSPSetting

from ..constants import AnalyticsTools
from .mixin import AnalyticsMixin


@override_settings(SOLO_CACHE=None, BASE_URL="https://example.com:8443/foo")
class ExpointsTests(AnalyticsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.json_cookies = []

        cls.json_csp = [
            {"directive": "default-src", "value": "https://*.expoints.nl"},
            {
                "directive": "font-src",
                "value": "https://*.expoints.nl https://cdn.expoints.nl",
            },
            {"directive": "script-src", "value": "https://*.expoints.nl"},
        ]

    def test_expoints_properly_enabled(self):
        self.config.expoints_organization_name = "Demodam"
        self.config.expoints_config_uuid = "1234"
        self.config.enable_expoints_analytics = True
        self.config.clean()
        self.config.save()

        for csp in self.json_csp:
            with self.subTest("Test creation of CSP", csp=csp):
                try:
                    CSPSetting.objects.get(
                        value=csp["value"],
                        directive=csp["directive"],
                        identifier=AnalyticsTools.expoints,
                    )
                except CSPSetting.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

    def test_expoints_properly_disabled(self):
        self.config.expoints_organization_name = "Demodam"
        self.config.expoints_config_uuid = "1234"

        # creation of cookies
        self.config.enable_expoints_analytics = True
        self.config.clean()
        self.config.save()

        # Deletion of cookies
        self.config.enable_expoints_analytics = False
        self.config.clean()
        self.config.save()

        for csp in self.json_csp:
            with self.subTest("Test deletion of CSP"):
                self.assertFalse(
                    CSPSetting.objects.filter(
                        value=csp["value"],
                        directive=csp["directive"],
                        identifier=AnalyticsTools.expoints,
                    ).exists()
                )

    def test_expoints_enabled_but_related_fields_are_not(self):
        self.config.enable_expoints_analytics = True
        self.config.expoints_organization_name = ""
        self.config.expoints_config_uuid = ""

        with self.assertRaises(ValidationError):
            self.config.clean()
