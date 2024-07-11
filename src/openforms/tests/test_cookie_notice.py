from io import StringIO

from django.core.management import call_command
from django.test import override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext as _

from asgiref.sync import sync_to_async
from cookie_consent.models import CookieGroup
from django_webtest import WebTest
from furl import furl
from playwright.async_api import expect

from openforms.analytics_tools.models import AnalyticsToolsConfiguration
from openforms.forms.tests.factories import FormFactory
from openforms.tests.e2e.base import E2ETestCase, browser_page
from openforms.tests.utils import NOOP_CACHES


@sync_to_async()
def setup_test_data(live_server_url: str):
    form = FormFactory.create()
    url = reverse("forms:form-detail", kwargs={"slug": form.slug})

    # load some default cookie groups and cookies
    call_command("loaddata", "cookie_consent", stdout=StringIO())

    config = AnalyticsToolsConfiguration.get_solo()

    # configure an analytics provider so that the JS snippets are not empty
    config.matomo_url = f"{live_server_url}/static"
    config.matomo_site_id = "1234"
    config.enable_matomo_site_analytics = True
    config.analytics_cookie_consent_group = CookieGroup.objects.get(
        varname="analytical"
    )

    config.save()

    return url


@override_settings(CACHES=NOOP_CACHES)
class CookieNoticeTests(E2ETestCase):
    async def test_anon_user_notice_rendered(self):
        path = await setup_test_data(self.live_server_url)
        url = f"{self.live_server_url}{path}"

        async with browser_page() as page:
            await page.goto(url)

            cookie_notice = page.get_by_role("region", name="Cookie notice")
            await expect(cookie_notice).to_be_visible()

    async def test_accept_reject_cookies(self):
        """
        Assert that the cookie notice is no longer visible once the user accepted or
        rejected them.
        """
        path = await setup_test_data(self.live_server_url)
        url = f"{self.live_server_url}{path}"

        with self.subTest(action="accept"):
            async with browser_page() as page:
                await page.goto(url)

                cookie_notice = page.get_by_role("region", name="Cookie notice")
                await cookie_notice.get_by_role("button", name="Accept all").click()
                await expect(cookie_notice).not_to_be_visible()

                # refreshing -> still not visible
                await page.reload()
                await expect(cookie_notice).not_to_be_visible()

        with self.subTest(action="decline"):
            async with browser_page() as page:
                await page.goto(url)

                cookie_notice = page.get_by_role("region", name="Cookie notice")
                await cookie_notice.get_by_role("button", name="Decline all").click()
                await expect(cookie_notice).not_to_be_visible()

                # refreshing -> still not visible
                await page.reload()
                await expect(cookie_notice).not_to_be_visible()

    async def test_analytics_snippets_not_rendered(self):
        """
        Assert that the analytics snippets are opt-in.

        Analytics snippets are only loaded after the user accepts the cookies.
        """
        path = await setup_test_data(self.live_server_url)
        url = f"{self.live_server_url}{path}"
        expected_script_src = f"{self.live_server_url}/static/matomo.js"

        with self.subTest(case="no cookies accepted or declined"):
            async with browser_page() as page:
                await page.goto(url)

                await expect(
                    page.locator(f'css=script[src="{expected_script_src}"]')
                ).not_to_be_attached()

        with self.subTest(case="cookies rejected"):
            async with browser_page() as page:
                await page.goto(url)
                await page.get_by_role("button", name="Decline all").click()

                await expect(
                    page.locator(f'css=script[src="{expected_script_src}"]')
                ).not_to_be_attached()

        with self.subTest(case="cookies accepted"):
            async with browser_page() as page:
                await page.goto(url)
                await page.get_by_role("button", name="Accept all").click()

                await expect(
                    page.locator(f'css=script[src="{expected_script_src}"]')
                ).to_be_attached()


@override_settings(CACHES=NOOP_CACHES)
class CookieListTests(WebTest):
    @tag("GHSA-c97h-m5qf-j8mf")
    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False,
        CORS_ALLOWED_ORIGINS=["https://external.domain.com"],
        ALLOWED_HOSTS=["testserver", "example.com"],
        IS_HTTPS=True,
    )
    def test_accept_reject_does_not_allow_open_redirect(self):
        # load some default cookie groups and cookies
        call_command("loaddata", "cookie_consent", stdout=StringIO())
        url = reverse("cookie_consent_cookie_group_list")
        allowed_redirects = (
            "https://example.com/foo/bar",
            "https://testserver/admin/",
            "/admin/",
        )
        blocked_redirects = (
            "http://example.com",
            "https://evil.com",
        )

        for allowed in allowed_redirects:
            with self.subTest(f"Allowed redirect to '{allowed}'"):
                self.renew_app()

                cookies_page = self.app.get(url, {"referer": allowed})
                parent = cookies_page.pyquery.find(
                    ".openforms-card__body a.utrecht-link--openforms"
                )
                link = parent(".utrecht-link--openforms")

                self.assertEqual(link.attr["href"], allowed)
                self.assertEqual(link.text(), _("Close"))

        for blocked in blocked_redirects:
            with self.subTest(f"Blockedredirect to '{blocked}'"):
                self.renew_app()

                cookies_page = self.app.get(url, {"referer": blocked})

                parent = cookies_page.pyquery.find(
                    ".openforms-card__body a.utrecht-link--openforms"
                )

                self.assertEqual(parent, [])

                for form in cookies_page.forms.values():
                    next_url = furl(form["next"].value)

                    self.assertEqual(next_url.args.get("referer", ""), "")
