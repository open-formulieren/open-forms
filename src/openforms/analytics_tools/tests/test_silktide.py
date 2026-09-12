from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

import csp.constants

from openforms.config.models import CSPSetting

from ..constants import AnalyticsTools
from .mixin import AnalyticsMixin


def parse_csp_policy(header_value):
    csp_values = {}
    for line in header_value.split("; "):
        directive, value = line.split(" ", maxsplit=1)
        csp_values[directive] = value.split(" ")
    return csp_values


@override_settings(SOLO_CACHE=None)
class SilktideTests(AnalyticsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.silktide_site_id = "e52e40921bf09be7dac44db29a73d173"
        cls.json_csp = [
            {"directive": "default-src", "value": "https://analytics.silktide.com"},
            {"directive": "script-src", "value": "https://analytics.silktide.com"},
            {"directive": "connect-src", "value": "https://a.eu.silktide.com"},
        ]

    def test_silktide_properly_enabled(self):
        self.config.silktide_site_id = self.silktide_site_id
        self.config.enable_silktide_analytics = True
        self.config.clean()
        self.config.save()

        for csp_setting in self.json_csp:
            with self.subTest("Test creation of CSP"):
                try:
                    CSPSetting.objects.get(
                        value=csp_setting["value"],
                        directive=csp_setting["directive"],
                        identifier=AnalyticsTools.silktide,
                    )
                except CSPSetting.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

    def test_silktide_properly_disabled(self):
        self.config.silktide_site_id = self.silktide_site_id

        self.config.enable_silktide_analytics = True
        self.config.clean()
        self.config.save()

        self.config.enable_silktide_analytics = False
        self.config.clean()
        self.config.save()

        for csp_setting in self.json_csp:
            with self.subTest("Test deletion of CSP"):
                self.assertFalse(
                    CSPSetting.objects.filter(
                        value=csp_setting["value"],
                        directive=csp_setting["directive"],
                        identifier=AnalyticsTools.silktide,
                    ).exists()
                )

    def test_silktide_enabled_but_related_fields_are_not(self):
        self.config.enable_silktide_analytics = True

        with self.assertRaises(ValidationError):
            self.config.clean()

    @override_settings(
        CONTENT_SECURITY_POLICY={
            "DIRECTIVES": {"default-src": [csp.constants.SELF]},
        },
        CONTENT_SECURITY_POLICY_REPORT_ONLY={},
    )
    def test_csp_header_includes_connect_src_endpoints(self):
        self.config.silktide_site_id = self.silktide_site_id
        self.config.enable_silktide_analytics = True
        self.config.clean()
        self.config.save()

        response = self.client.get("/")

        csp_policy = parse_csp_policy(response.headers["Content-Security-Policy"])
        self.assertIn("https://analytics.silktide.com", csp_policy["script-src"])
        self.assertIn("https://a.eu.silktide.com", csp_policy["connect-src"])
        self.assertNotIn("https://a.us.silktide.com", csp_policy["connect-src"])
        self.assertNotIn("https://a.au.silktide.com", csp_policy["connect-src"])
