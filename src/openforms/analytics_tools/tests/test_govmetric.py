from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from cookie_consent.models import Cookie

from openforms.config.models import CSPSetting

from ..constants import AnalyticsTools
from .mixin import AnalyticsMixin


@override_settings(SOLO_CACHE=None, BASE_URL="https://example.com:8443/foo")
class GovMetricTests(AnalyticsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.json_cookies = [
            {"name": "_pk_id.1234.8809", "path": "/"},
            {"name": "_pk_ses.1234.8809", "path": "/"},
        ]

        cls.json_csp = [
            {"directive": "default-src", "value": "https://*.govmetric.com"},
            {"directive": "script-src", "value": "https://*.govmetric.com"},
            {"directive": "frame-src", "value": "https://*.govmetric.com"},
            {"directive": "img-src", "value": "https://www.klantinfocus.nl"},
        ]

    def test_govmetric_properly_enabled(self):
        self.config.govmetric_source_id_form_finished = "1234"
        self.config.govmetric_source_id_form_aborted = "1234"
        self.config.enable_govmetric_analytics = True
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
                        identifier=AnalyticsTools.govmetric,
                    )
                except CSPSetting.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

    def test_govmetric_properly_disabled(self):
        self.config.govmetric_source_id_form_finished = "1234"
        self.config.govmetric_source_id_form_aborted = "1234"

        # creation of cookies
        self.config.enable_govmetric_analytics = True
        self.config.clean()
        self.config.save()

        # Deletion of cookies
        self.config.enable_govmetric_analytics = False
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
                        identifier=AnalyticsTools.govmetric,
                    ).exists()
                )

    def test_govmetric_enabled_but_related_fields_are_not(self):
        self.config.enable_govmetric_analytics = True
        self.config.govmetric_source_id_form_finished = ""
        self.config.govmetric_source_id_form_aborted = ""

        with self.assertRaises(ValidationError):
            self.config.clean()

    def test_govmetric_enabled_in_only_one_language_raises_error(self):
        self.config.enable_govmetric_analytics = True
        self.config.govmetric_source_id_form_finished_en = "1234"
        self.config.govmetric_source_id_form_finished_nl = ""
        self.config.govmetric_source_id_form_aborted_en = "1234"
        self.config.govmetric_source_id_form_aborted_nl = ""

        with self.assertRaises(ValidationError):
            self.config.clean()
