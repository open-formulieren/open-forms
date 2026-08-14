from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser

from ..factories import FormFactory
from .helpers import close_modal, drag_and_drop_component, open_fieldset


class FormDesignerComponentDefinitionTests(E2ETestCase):
    async def test_warning_multiple_cosign(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            return FormFactory.create(
                name="Form Test Cosign",
                name_nl="Formulier Test Cosign",
                generate_minimal_setup=True,
                formstep__form_definition__configuration={"components": []},
                authentication_backend="digid",
            )

        await create_superuser()
        form = await setUpTestData()
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await page.get_by_role("tab", name="Steps and Fields").click()

            await page.get_by_text("Special fields").click()

            # Add first component
            await drag_and_drop_component(page, "Co-sign", nth=0)
            await close_modal(page, "Save")

            warning_node = page.get_by_role("list").filter(
                has=page.locator("css=.warning")
            )

            await expect(warning_node).to_be_hidden()

            # Add second component
            await drag_and_drop_component(page, "Co-sign", nth=0)
            await close_modal(page, "Save")

            # Check that a warning has appeared
            await expect(warning_node).to_be_visible()

    async def test_missing_auth_plugin_warning(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            return FormFactory.create(
                name="Form Test Cosign",
                name_nl="Formulier Test Cosign",
                generate_minimal_setup=True,
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "id": "cc5d31e6-c2eb-4292-af39-35819be3db1a",
                            "type": "cosign",
                            "key": "cosign",
                            "label": "cosign",
                        }
                    ]
                },
                authentication_backend="digid",
            )

        await create_superuser()
        form = await setUpTestData()
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))

            warning_node = page.get_by_role("list").filter(
                has=page.locator("css=.warning")
            )

            # Check that there is no warning
            await expect(warning_node).not_to_be_visible()

            await open_fieldset(page, "Authentication")
            await page.get_by_role("checkbox", name="DigiD", checked=True).click()

            # Check that the warning has appeared
            await expect(warning_node).to_be_visible()
