from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser

from ..factories import FormFactory
from .test_form_designer import drag_and_drop_component


class FormDesignerComponentDefinitionTests(E2ETestCase):
    async def test_file_upload_component_has_label_of_mime_types(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            return FormFactory.create(
                name="Form Test",
                name_nl="Formulier Test",
                generate_minimal_setup=True,
                formstep__form_definition__configuration={"components": []},
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

            await drag_and_drop_component(page, "Bestandsupload")
            await page.get_by_role("link", name="Bestand").click()
            label = page.get_by_text("Bestandstypen", exact=True).first
            field = label.locator("..")  # grab the parent
            dropdown = field.get_by_role("combobox")
            await dropdown.click()
            await dropdown.get_by_text(".pdf").click()
            await dropdown.blur()

            # Save component
            await page.get_by_role("button", name="Opslaan").click()

            # Save form
            await page.locator('css=[name="_save"]').click()

        @sync_to_async
        def assertConfigurationHasLabels():
            form.refresh_from_db()
            configuration = form.formstep_set.get().form_definition.configuration
            component = configuration["components"][0]
            self.assertEqual(component["file"]["type"], ["application/pdf"])
            self.assertIn("allowedTypesLabels", component["file"])
            self.assertEqual(
                component["file"]["allowedTypesLabels"],
                [".pdf"],
            )

        await assertConfigurationHasLabels()

    async def test_warning_multiple_cosign(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            return FormFactory.create(
                name="Form Test Cosign",
                name_nl="Formulier Test Cosign",
                generate_minimal_setup=True,
                formstep__form_definition__configuration={"components": []},
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

            await page.get_by_text("Speciale velden").click()

            # Add first component
            await drag_and_drop_component(page, "Mede-ondertekenen")
            await page.get_by_role("button", name="Opslaan").click()

            warning_node = page.get_by_role("list").filter(
                has=page.locator("css=.warning")
            )

            await expect(warning_node).to_be_hidden()

            # Add second component
            await drag_and_drop_component(page, "Mede-ondertekenen")
            await page.get_by_role("button", name="Opslaan").click()

            # Check that a warning has appeared
            await expect(warning_node).to_be_visible()
