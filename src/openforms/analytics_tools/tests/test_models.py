import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from cookie_consent.models import Cookie, CookieGroup

from openforms.config.models import CSPSetting

from ..constants import AnalyticsTools
from ..models import AnalyticsToolsConfiguration
from ..utils import get_cookies, get_csp, get_domain_hash


@override_settings(
    SOLO_CACHE=None,
)
class GoogleAnalyticsTests(TestCase):
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

    def test_google_analytics_properly_enabled(self):

        self.config.enable_google_analytics = True
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

    def test_google_analytics_properly_disabled(self):

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
                        value=csp["value"], directive=csp["directive"]
                    ).exists()
                )

    def test_google_analytics_enabled_but_related_fields_are_not(self):
        self.config.enable_google_analytics = True
        self.config.gtm_code = ""

        with self.assertRaises(ValidationError):
            self.config.clean()


@override_settings(
    SOLO_CACHE=None,
)
class MatomoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.matomo_url = "https://example.com"
        cls.matomo_site_id = 1234
        string_replacements_list = [
            ("SITE_ID", cls.matomo_site_id),
            ("SITE_URL", cls.matomo_url),
            (
                "DOMAIN_HASH",
                lambda cookie: get_domain_hash(
                    settings.ALLOWED_HOSTS[0], cookie_path=cookie["path"]
                ),
            ),
        ]
        cls.json_cookies = get_cookies(
            analytics_tool=AnalyticsTools.matomo,
            string_replacement_list=string_replacements_list,
        )

        cls.json_csp = get_csp(
            analytics_tool=AnalyticsTools.matomo,
            string_replacement_list=string_replacements_list,
        )

    def setUp(self):
        super().setUp()
        self.config = AnalyticsToolsConfiguration.get_solo()
        self.config.analytics_cookie_consent_group = CookieGroup.objects.get(
            varname="analytical"
        )
        self.config.matomo_url = self.matomo_url
        self.config.matomo_site_id = self.matomo_site_id
        self.addCleanup(lambda: AnalyticsToolsConfiguration.get_solo().delete())

    def test_matomo_properly_enabled(self):

        self.config.enable_matomo_site_analytics = True
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

    def test_matomo_properly_disabled(self):

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
                        value=csp["value"], directive=csp["directive"]
                    ).exists()
                )

    def test_matomo_enabled_but_related_fields_are_not(self):
        self.config.enable_matomo_site_analytics = True
        self.config.matomo_url = ""

        with self.assertRaises(ValidationError):
            self.config.clean()


@override_settings(
    SOLO_CACHE=None,
)
class PiwikTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.piwik_url = "https://example.com"
        cls.piwik_site_id = 1234
        string_replacements_list = [
            ("SITE_ID", cls.piwik_site_id),
            ("SITE_URL", cls.piwik_url),
            (
                "DOMAIN_HASH",
                lambda cookie: get_domain_hash(
                    settings.ALLOWED_HOSTS[0], cookie_path=cookie["path"]
                ),
            ),
        ]
        cls.json_cookies = get_cookies(
            analytics_tool=AnalyticsTools.piwik,
            string_replacement_list=string_replacements_list,
        )

        cls.json_csp = get_csp(
            analytics_tool=AnalyticsTools.piwik,
            string_replacement_list=string_replacements_list,
        )

    def setUp(self):
        super().setUp()
        self.config = AnalyticsToolsConfiguration.get_solo()
        self.config.analytics_cookie_consent_group = CookieGroup.objects.get(
            varname="analytical"
        )
        self.config.piwik_url = self.piwik_url
        self.config.piwik_site_id = self.piwik_site_id
        self.addCleanup(lambda: AnalyticsToolsConfiguration.get_solo().delete())

    def test_piwik_properly_enabled(self):

        self.config.enable_piwik_site_analytics = True
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

    def test_piwik_properly_disabled(self):

        # creation of cookies
        self.config.enable_piwik_site_analytics = True
        self.config.clean()
        self.config.save()

        # Deletion of cookies
        self.config.enable_piwik_site_analytics = False
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

    def test_piwik_enabled_but_related_fields_are_not(self):
        self.config.enable_piwik_site_analytics = True
        self.config.piwik_url = ""

        with self.assertRaises(ValidationError):
            self.config.clean()


@override_settings(
    SOLO_CACHE=None,
)
class PiwikProTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.piwik_pro_url = "https://example.com"
        cls.piwik_pro_site_id = uuid.uuid4()
        string_replacements_list = [
            ("SITE_ID", cls.piwik_pro_site_id),
            ("SITE_URL", cls.piwik_pro_url),
            (
                "DOMAIN_HASH",
                lambda cookie: get_domain_hash(
                    settings.ALLOWED_HOSTS[0], cookie_path=cookie["path"]
                ),
            ),
        ]
        cls.json_cookies = get_cookies(
            analytics_tool=AnalyticsTools.piwik_pro,
            string_replacement_list=string_replacements_list,
        )

        cls.json_csp = get_csp(
            analytics_tool=AnalyticsTools.piwik_pro,
            string_replacement_list=string_replacements_list,
        )

    def setUp(self):
        super().setUp()
        self.config = AnalyticsToolsConfiguration.get_solo()
        self.config.analytics_cookie_consent_group = CookieGroup.objects.get(
            varname="analytical"
        )
        self.config.piwik_pro_url = self.piwik_pro_url
        self.config.piwik_pro_site_id = self.piwik_pro_site_id
        self.addCleanup(lambda: AnalyticsToolsConfiguration.get_solo().delete())

    def test_piwik_pro_properly_enabled(self):

        self.config.enable_piwik_pro_site_analytics = True
        self.config.clean()
        self.config.save()

        for cookie in self.json_cookies:
            with self.subTest("Test creation of cookies"):
                try:
                    Cookie.objects.filter(name=cookie["name"])
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
        self.config.piwik_pro_url = ""

        with self.assertRaises(ValidationError):
            self.config.clean()


@override_settings(
    SOLO_CACHE=None,
)
class SiteImproveTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.json_cookies = get_cookies(
            analytics_tool=AnalyticsTools.siteimprove, string_replacement_list=[]
        )

        cls.json_csp = get_csp(
            analytics_tool=AnalyticsTools.siteimprove, string_replacement_list=[]
        )

    def setUp(self):
        super().setUp()
        self.config = AnalyticsToolsConfiguration.get_solo()
        self.config.analytics_cookie_consent_group = CookieGroup.objects.get(
            varname="analytical"
        )
        self.config.siteimprove_id = 1234
        self.addCleanup(lambda: AnalyticsToolsConfiguration.get_solo().delete())

    def test_site_improve_properly_enabled(self):

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
        self.config.siteimprove_id = None

        with self.assertRaises(ValidationError):
            self.config.clean()
