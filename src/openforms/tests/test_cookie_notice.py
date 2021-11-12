from io import StringIO

from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from cookie_consent.cache import delete_cache
from cookie_consent.models import CookieGroup
from django_webtest import WebTest

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory
from openforms.tests.utils import NOOP_CACHES


@override_settings(CACHES=NOOP_CACHES)
class CookieNoticeTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.form = FormFactory.create()
        cls.url = reverse("forms:form-detail", kwargs={"slug": cls.form.slug})

        # load some default cookie groups and cookies
        call_command("loaddata", "cookie_consent", stdout=StringIO())

        config = GlobalConfiguration.get_solo()

        # configure analytics so that the JS snippets are not empty
        config.gtm_code = "GTM-XXXX"
        config.ga_code = "UA-XXXXX-Y"
        config.matomo_url = "https://example.com"
        config.matomo_site_id = "1234"
        config.piwik_url = "https://example.com"
        config.piwik_site_id = "1234"
        config.siteimprove_id = "1234"
        config.analytics_cookie_consent_group = CookieGroup.objects.get(
            varname="analytical"
        )
        config.save()

        # workaround for https://github.com/bmihelac/django-cookie-consent/issues/41
        # the cache instance is resolved at import time rather than at runtime.
        delete_cache()

    def test_anon_user_notice_rendered(self):
        form_page = self.app.get(self.url)

        cookie_notice = form_page.pyquery(".cookie-notice")

        # check that the notice is present
        self.assertTrue(bool(cookie_notice))

    def test_accept_reject_cookies(self):
        """
        Assert that the cookie notice is no longer visible once the user accepted or
        rejected them.
        """
        with self.subTest(action="accept"):
            form_page = self.app.get(self.url)

            accept_form = form_page.forms[0]
            assert "accept" in accept_form.action

            refreshed_form_page = accept_form.submit().follow()

            self.assertEqual(refreshed_form_page.request.path, self.url)
            self.assertFalse(refreshed_form_page.pyquery(".cookie-notice"))

        self.renew_app()

        with self.subTest(action="decline"):
            form_page = self.app.get(self.url)

            decline_form = form_page.forms[1]
            assert "decline" in decline_form.action

            refreshed_form_page = decline_form.submit().follow()

            self.assertEqual(refreshed_form_page.request.path, self.url)
            self.assertFalse(refreshed_form_page.pyquery(".cookie-notice"))

    def test_analytics_snippets_not_rendered(self):
        """
        Assert that the analytics snippets are opt-in.

        Analytics snippets are only loaded after the user accepts the cookies.
        """
        with self.subTest(case="no cookies accepted or declined"):
            form_page = self.app.get(self.url)

            self.assertTemplateNotUsed(form_page, "includes/analytics/all_head.html")
            self.assertTemplateNotUsed(form_page, "includes/analytics/all_bottom.html")

        with self.subTest(case="cookies rejected"):
            decline_form = form_page.forms[1]
            assert "decline" in decline_form.action

            refreshed_form_page = decline_form.submit().follow()

            self.assertTemplateNotUsed(
                refreshed_form_page, "includes/analytics/all_head.html"
            )
            self.assertTemplateNotUsed(
                refreshed_form_page, "includes/analytics/all_bottom.html"
            )

        self.renew_app()

        with self.subTest(case="cookies accepted"):
            form_page = self.app.get(self.url)

            accept_form = form_page.forms[0]
            assert "accept" in accept_form.action

            refreshed_form_page = accept_form.submit().follow()

            self.assertTemplateUsed(
                refreshed_form_page, "includes/analytics/all_head.html"
            )
            self.assertTemplateUsed(
                refreshed_form_page, "includes/analytics/all_bottom.html"
            )
