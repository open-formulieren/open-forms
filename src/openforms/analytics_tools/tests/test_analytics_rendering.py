from django.test import override_settings
from django.urls import reverse

from cookie_consent.models import CookieGroup
from django_webtest import WebTest

from openforms.analytics_tools.models import AnalyticsToolsConfiguration
from openforms.forms.tests.factories import FormFactory
from openforms.tests.utils import NOOP_CACHES


@override_settings(CACHES=NOOP_CACHES)
class AnalyticsToolsRenderingTest(WebTest):
    """Integration tests for rendering of analytics snippets.

    The tests check that the analytics snippets are rendered if they are
    enabled (by the admin) and cookies are accepted (by the user). They
    do *not* test whether the scripts are properly executed, which requires
    either manual testing or functional tests with Playwright.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        form = FormFactory.create()
        cls.url = reverse("forms:form-detail", kwargs={"slug": form.slug})
        config = AnalyticsToolsConfiguration.get_solo()
        config.analytics_cookie_consent_group, _ = CookieGroup.objects.get_or_create(
            varname="analytical"
        )
        config.save()
        cls.config = config

    def test_google_analytics_rendering(self):
        """Assert that the Google Analytics script is rendered"""

        # Enable and configure Google analytics
        self.config.enable_google_analytics = True
        self.config.gtm_code = "GTM-XXXX"
        self.config.ga_code = "UA-XXXXX-Y"
        self.config.save()

        form_page = self.app.get(self.url)

        google_tag_manager = form_page.pyquery("#google-tag-manager")
        google_analytics = form_page.pyquery("#google-analytics")
        self.assertTrue(google_tag_manager.is_("script"))
        self.assertTrue(google_analytics.is_("script"))

        # Regression test for #1587
        with self.subTest("script CSP nonces"):
            scripts = form_page.pyquery("script[nonce]")
            for script in scripts:
                self.assertTrue(bool(script.attrib["nonce"]))

    def test_matomo_rendering(self):
        """Assert that the Matomo script is rendered"""

        # Enable and configure Matomo
        self.config.enable_matomo_site_analytics = True
        self.config.matomo_site_id = 1234
        self.config.matomo_url = self.url
        self.config.save()

        # Accept cookies
        form_page = self.app.get(self.url)

        matomo = form_page.pyquery("#matomo-analytics")
        self.assertTrue(matomo.is_("script"))

    def test_piwik_pro_rendering(self):
        """Assert that the Piwik Pro script is rendered"""

        # Enable and configure Piwik Pro
        self.config.enable_piwik_pro_site_analytics = True
        self.config.piwik_pro_site_id = 1234
        self.config.piwik_pro_url = self.url
        self.config.save()

        # Accept cookies
        form_page = self.app.get(self.url)

        piwik_pro = form_page.pyquery("#piwik-pro-analytics")
        self.assertTrue(piwik_pro.is_("script"))

    def test_piwik_pro_tag_manager_rendering(self):
        """Assert that the Piwik Pro Tag Manager scripts are rendered"""

        # Configure Piwik Pro site ID and URL
        self.config.piwik_pro_site_id = 1234
        self.config.piwik_pro_url = self.url
        # Enable Tag manager
        self.config.enable_piwik_pro_tag_manager = True
        self.config.save()

        # Accept cookies
        form_page = self.app.get(self.url)

        tag_manager_async = form_page.pyquery("#piwik-pro-tag-manager-async")
        self.assertTrue(tag_manager_async.is_("script"))

    def test_piwik_rendering(self):
        """Assert that the Piwik script is rendered"""

        # Enable and configure Piwik
        self.config.enable_piwik_site_analytics = True
        self.config.piwik_site_id = 1234
        self.config.piwik_url = self.url
        self.config.save()

        # Accept cookies
        form_page = self.app.get(self.url)

        piwik = form_page.pyquery("#piwik-analytics")
        self.assertTrue(piwik.is_("script"))

    def test_site_improve_rendering(self):
        """Assert that the Siteimprove script is rendered"""

        # Enable and configure Siteimprove
        self.config.enable_siteimprove_analytics = True
        self.config.siteimprove_id = 1234
        self.config.siteimprove_url = self.url
        self.config.save()

        # Accept cookies
        form_page = self.app.get(self.url)

        siteimprove = form_page.pyquery("#siteimprove-analytics")
        self.assertTrue(siteimprove.is_("script"))

    def test_expoints_rendering(self):
        """Assert that the Expoints script is rendered"""

        # Enable and configure Expoints
        self.config.enable_expoints_analytics = True
        self.config.expoints_organization_name = "Demodam"
        self.config.expoints_config_uuid = "1234"
        self.config.save()

        # Accept cookies
        form_page = self.app.get(self.url)

        siteimprove = form_page.pyquery("#expoints-analytics")
        self.assertTrue(siteimprove.is_("script"))
