from django.test import tag
from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.config.models import GlobalConfiguration

from .base import E2ETestCase, browser_page, create_superuser


class TinyMCEConfigurationTests(E2ETestCase):

    def setUp(self):
        super().setUp()

        self.addCleanup(GlobalConfiguration.clear_cache)

    @tag("gh-4390")
    async def test_link_handling(self):
        """
        Test that hyperlinks in WYSIWYG content are handled appropriately.

        1. Links with the same domain/prefix as where the admin is running must stay
           absolute, and not be converted to relative paths. See #4368 for more
           information.
        2. Link targets may be template variables, like ``{{ continue_ url }}``, these
           may not be post-processed and get prefixed with the (current) location to
           make them absolute.
        """

        @sync_to_async
        def setUpTestData():
            config = GlobalConfiguration.get_solo()
            config.save_form_email_content_en = f"""
            <p><a href="{self.live_server_url}/some-form-slug/">Go to form<a><p>
            <p><a href="{{{{ some_variable }}}}">Variable link</a></p>
            """
            config.save()

        await setUpTestData()

        admin_url = furl(self.live_server_url) / reverse(
            "admin:config_globalconfiguration_change", args=(1,)
        )

        await create_superuser()
        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))

            content_frame = page.frame_locator("#id_save_form_email_content_en_ifr")
            await expect(content_frame.get_by_label("Rich Text Area.")).to_be_visible()

            absolute_link = content_frame.get_by_role("link", name="Go to form")
            await expect(absolute_link).to_be_visible()
            await expect(absolute_link).to_have_attribute(
                "data-mce-href", f"{self.live_server_url}/some-form-slug/"
            )

            variable_link = content_frame.get_by_role("link", name="Variable link")
            await expect(variable_link).to_be_visible()
            await expect(variable_link).to_have_attribute(
                "data-mce-href", "{{ some_variable }}"
            )
