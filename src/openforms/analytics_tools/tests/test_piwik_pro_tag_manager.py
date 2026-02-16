from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

import csp.constants
from cookie_consent.models import Cookie
from rest_framework import status
from rest_framework.test import APITestCase

from openforms.config.models import CSPSetting
from openforms.forms.tests.factories import FormFactory
from openforms.tests.test_csp import CSPMixin

from ..constants import AnalyticsTools
from .mixin import AnalyticsMixin


@override_settings(SOLO_CACHE=None, BASE_URL="https://example.com:8443/foo")
class PiwikProTagManagerTests(AnalyticsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.piwik_pro_url = "https://example.com"
        cls.json_cookies = [
            {"name": "_pk_id.771cbcaa-7315-4663-ba47-88f9a8cc158c.8809", "path": "/"},
            {"name": "_pk_ses.771cbcaa-7315-4663-ba47-88f9a8cc158c.8809", "path": "/"},
        ]

        cls.json_csp = [
            {"directive": "default-src", "value": cls.piwik_pro_url},
        ]

    def test_piwik_pro_tag_manager_properly_enabled(self):
        self.config.piwik_pro_url = self.piwik_pro_url
        self.config.piwik_pro_site_id = "771cbcaa-7315-4663-ba47-88f9a8cc158c"

        self.config.enable_piwik_pro_tag_manager = True
        self.config.clean()
        self.config.save()

        for cookie in self.json_cookies:
            with self.subTest("Test creation of cookies"):
                try:
                    Cookie.objects.get(name=cookie["name"])
                except Cookie.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

        for directive in self.json_csp:
            with self.subTest("Test creation of CSP"):
                try:
                    CSPSetting.objects.get(
                        value=directive["value"],
                        directive=directive["directive"],
                        identifier=AnalyticsTools.piwik_pro_tag_manager,
                    )
                except CSPSetting.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

    def test_piwik_pro_tag_manager_properly_disabled(self):
        self.config.piwik_pro_url = self.piwik_pro_url
        self.config.piwik_pro_site_id = "771cbcaa-7315-4663-ba47-88f9a8cc158c"

        # creation of cookies
        self.config.enable_piwik_pro_tag_manager = True
        self.config.clean()
        self.config.save()

        # Deletion of cookies
        self.config.enable_piwik_pro_tag_manager = False
        self.config.clean()
        self.config.save()

        for cookie in self.json_cookies:
            with self.subTest("Test deletion of cookies"):
                self.assertFalse(Cookie.objects.filter(name=cookie["name"]).exists())

        for directive in self.json_csp:
            with self.subTest("Test deletion of CSP"):
                self.assertFalse(
                    CSPSetting.objects.filter(
                        value=directive["value"],
                        directive=directive["directive"],
                        identifier=AnalyticsTools.piwik_pro_tag_manager,
                    ).exists()
                )

    def test_piwik_pro_tag_manager_enabled_but_related_fields_are_not(self):
        self.config.enable_piwik_pro_tag_manager = True

        with self.assertRaises(ValidationError):
            self.config.clean()

    def test_piwik_pro_analytics_and_tag_manager_exclusive(self):
        self.config.enable_piwik_pro_site_analytics = True
        self.config.enable_piwik_pro_tag_manager = True
        self.config.piwik_pro_url = self.piwik_pro_url
        self.config.piwik_pro_site_id = "771cbcaa-7315-4663-ba47-88f9a8cc158c"

        with self.assertRaises(ValidationError) as cm:
            self.config.clean()
        self.assertEqual(cm.exception.code, "invalid_together")


@override_settings(
    CONTENT_SECURITY_POLICY={"DIRECTIVES": {"default-src": [csp.constants.SELF]}},
    CONTENT_SECURITY_POLICY_REPORT_ONLY={},
)
class CanLoadFormWithAnalyticsCSPTests(CSPMixin, APITestCase):
    def test_loading_form_still_has_self_in_default_src(self):
        csp_setting = CSPSetting(value="https://piwikpro.com", directive="default-src")
        csp_setting.save()

        form = FormFactory.create()

        response = self.client.get(
            reverse("core:form-detail", kwargs={"slug": form.slug})
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn(
            "default-src 'self' https://piwikpro.com",
            response.headers["Content-Security-Policy"],
        )
