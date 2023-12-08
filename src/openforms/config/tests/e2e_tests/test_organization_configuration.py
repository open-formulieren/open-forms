from textwrap import dedent

from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser

from ...models import Theme
from ..factories import ThemeFactory


class OrganizationConfigurationTests(E2ETestCase):
    async def test_design_token_editor_integration(self):
        @sync_to_async
        def setupTestData():
            theme = ThemeFactory.create()
            return theme

        await create_superuser()
        theme = await setupTestData()

        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:config_theme_change", args=(theme.pk,))
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))

            await page.get_by_role("button", name="Open editor").click()
            modal = page.get_by_role("dialog")
            await expect(modal).to_contain_text("Design token values")
            await modal.get_by_label("All", exact=True).click()
            await expect(modal).to_contain_text("utrecht-link")

            # edit a design token
            token_to_edit = page.get_by_text("of.utrecht-link.font-family")
            token_row = token_to_edit.locator("../..")
            await token_row.get_by_role("button").click()
            await token_row.get_by_placeholder("Fira Sans, Calibri, sans-serif").fill(
                "Roboto"
            )

            await modal.get_by_role("button", name="Save changes").click()

            # check that the JSONField is updated
            expected_json = dedent(
                """
            {
              "of": {
                "utrecht-link": {
                  "font-family": {
                    "value": "Roboto"
                  }
                }
              }
            }
            """
            ).strip()
            await expect(page.get_by_label("Design token values:")).to_have_value(
                expected_json
            )

            await page.get_by_role("button", name="Save", exact=True).click()

        @sync_to_async
        def assertState():
            theme = Theme.objects.get()

            self.assertEqual(
                theme.design_token_values,
                {"of": {"utrecht-link": {"font-family": {"value": "Roboto"}}}},
            )

        await assertState()
