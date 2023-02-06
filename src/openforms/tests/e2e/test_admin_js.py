from django.urls import reverse

from furl import furl
from playwright.async_api import expect

from .base import E2ETestCase, browser_page, create_superuser


class AdminJSTests(E2ETestCase):
    async def test_admin_pages_with_js_bundle_dont_crash(self):
        # list of URLs that are known to include the Webpack admin JS bundle
        page_urls = (
            reverse("admin:forms_form_add"),
            reverse("admin:forms_formdefinition_add"),
            reverse("admin:config_globalconfiguration_change", args=(1,)),
        )

        await create_superuser()
        async with browser_page() as page:
            await self._admin_login(page)

            for page_path in page_urls:
                with self.subTest(admin_url=page_path):
                    full_url = furl(self.live_server_url) / page_path
                    await page.goto(str(full_url))

                    marker = page.get_by_test_id("e2e-test-id")
                    await expect(marker).to_have_count(1, timeout=500)
