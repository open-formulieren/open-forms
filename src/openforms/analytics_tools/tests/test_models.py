from django.test import TestCase, override_settings

from cookie_consent.models import Cookie, CookieGroup

from openforms.config.models import CSPSetting

from ..constants import AnalyticsTools
from ..models import AnalyticsToolsConfiguration
from ..utils import get_cookies, get_csp


@override_settings(
    SOLO_CACHE=None,
)
class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.json_cookies = get_cookies(
            analytics_tool=AnalyticsTools.google_analytics, string_replacement_list=[]
        )
        cls.json_csp = get_csp(
            analytics_tool=AnalyticsTools.google_analytics, string_replacement_list=[]
        )

    def setUp(self):
        super().setUp()
        self.config = AnalyticsToolsConfiguration.get_solo()
        self.config.analytics_cookie_consent_group = CookieGroup.objects.get(
            varname="analytical"
        )
        self.config.gtm_code = "GTM-XXXX"
        self.config.ga_code = "UA-XXXXX-Y"
        self.addCleanup(lambda: AnalyticsToolsConfiguration.get_solo().delete())

    def test_analytics_tool_properly_enabled(self):

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
                    CSPSetting.objects.get(value=csp["value"])
                except CSPSetting.DoesNotExist as e:
                    self.fail(f"Unexpected exception : {e}")

    def test_analytics_tool_properly_disabled(self):

        # creation of cookies
        self.config.enable_google_analytics = True
        self.config.save()

        # Deletion of cookies
        self.config.enable_google_analytics = False
        self.config.save()

        for cookie in self.json_cookies:
            with self.subTest("Test deletion of cookies"):
                self.assertFalse(Cookie.objects.filter(name=cookie["name"]).exists())

        for csp in self.json_csp:
            with self.subTest("Test deletion of CSP"):
                self.assertFalse(CSPSetting.objects.filter(value=csp["value"]).exists())

    def test_analytics_tool_enabled_but_related_fields_are_not(self):
        self.config.enable_google_analytics = True
        self.config.gtm_code = ""
        self.config.save()

        for cookie in self.json_cookies:
            with self.subTest("Test deletion of cookies"):
                self.assertFalse(Cookie.objects.filter(name=cookie["name"]).exists())

        for csp in self.json_csp:
            with self.subTest("Test deletion of CSP"):
                self.assertFalse(CSPSetting.objects.filter(value=csp["value"]).exists())
