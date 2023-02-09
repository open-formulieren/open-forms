from django.urls import reverse

from cookie_consent.models import CookieGroup
from django_webtest import WebTest

from openforms.analytics_tools.models import AnalyticsToolsConfiguration
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.cache import clear_caches


class AnalyticsToolsRenderingTest(WebTest):
    """Integration tests for rendering of analytics snippets.

    The tests check that the analytics snippets are rendered if they are
    enabled (by the admin) and cookies are accepted (by the user). They
    do *not* test whether the scripts are properly executed, which requires
    either manual testing or functional tests with Playwright.
    """

    @classmethod
    def setUpTestData(cls):
        clear_caches()
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

        # Accept cookies
        form_page = self.app.get(self.url)
        accept_form = form_page.forms[0]
        refreshed_form_page = accept_form.submit().follow()

        google_tag_manager = refreshed_form_page.pyquery("#google-tag-manager")
        google_analytics = refreshed_form_page.pyquery("#google-analytics")

        self.assertTrue(google_tag_manager.is_("script"))
        self.assertTrue(google_analytics.is_("script"))

    def test_matomo_rendering(self):
        """Assert that the Matomo script is rendered"""

        # Enable and configure Matomo
        self.config.enable_matomo_site_analytics = True
        self.config.matomo_site_id = 1234
        self.config.matomo_url = self.url
        self.config.save()

        # Accept cookies
        form_page = self.app.get(self.url)
        accept_form = form_page.forms[0]
        refreshed_form_page = accept_form.submit().follow()

        matomo = refreshed_form_page.pyquery("#matomo-analytics")

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
        accept_form = form_page.forms[0]
        refreshed_form_page = accept_form.submit().follow()

        piwik_pro = refreshed_form_page.pyquery("#piwik-pro-analytics")

        self.assertTrue(piwik_pro.is_("script"))

    def test_piwik_rendering(self):
        """Assert that the Piwik script is rendered"""

        # Enable and configure Piwik
        self.config.enable_piwik_site_analytics = True
        self.config.piwik_site_id = 1234
        self.config.piwik_url = self.url
        self.config.save()

        # Accept cookies
        form_page = self.app.get(self.url)
        accept_form = form_page.forms[0]
        refreshed_form_page = accept_form.submit().follow()

        piwik = refreshed_form_page.pyquery("#piwik-analytics")

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
        accept_form = form_page.forms[0]
        refreshed_form_page = accept_form.submit().follow()

        siteimprove = refreshed_form_page.pyquery("#siteimprove-analytics")

        self.assertTrue(siteimprove.is_("script"))
