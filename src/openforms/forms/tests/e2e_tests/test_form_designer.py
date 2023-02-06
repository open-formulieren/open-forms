import re
from contextlib import contextmanager

from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser

from ..factories import FormFactory


@contextmanager
def phase(desc: str):
    yield


class FormDesignerComponentTranslationTests(E2ETestCase):
    async def test_editing_translatable_properties(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "field1",
                            "label": "Field 1",
                            "description": "Description 1",
                        },
                        {
                            "type": "select",
                            "key": "field2",
                            "label": "Field 2",
                            "description": "Description 2",
                            "data": {
                                "values": [
                                    {"value": "option1", "label": "Option 1"},
                                    {"value": "option2", "label": "Option 2"},
                                ]
                            },
                        },
                    ],
                },
            )
            return form

        await create_superuser()
        form = await setUpTestData()
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await page.get_by_role("tab", name="Steps and fields").click()

            with phase("Textfield component checks"):
                # hover over component to bring up action icons
                await page.get_by_text("Field 1").hover()
                # formio doesn't have accessible roles here, so use CSS selector
                await page.locator('css=[ref="editComponent"]').locator(
                    "visible=true"
                ).click()

                # check that the modal is open now
                await expect(page.locator("css=.formio-dialog-content")).to_have_count(
                    1
                )

                # find and click translations tab
                await page.get_by_role("link", name="Vertalingen").click()

                # check the values of the translation inputs
                literal1 = page.locator(
                    'css=[name="data[openForms.translations.nl][0]"]'
                )
                translation1 = page.locator(
                    'css=[name="data[openForms.translations.nl][0][translation]"]'
                )
                literal2 = page.locator(
                    'css=[name="data[openForms.translations.nl][1]"]'
                )
                translation2 = page.locator(
                    'css=[name="data[openForms.translations.nl][1][translation]"]'
                )
                await expect(literal1).to_have_value("Field 1")
                await expect(translation1).to_have_value("")
                await expect(literal2).to_have_value("Description 1")
                await expect(translation2).to_have_value("")

                # edit textfield label literal
                await page.get_by_role("link", name="Basis").click()
                await page.get_by_label("Label").fill("Field label")

                # translations tab needs to be updated
                await page.get_by_role("link", name="Vertalingen").click()
                await expect(literal1).to_have_value("Description 1")
                await expect(translation1).to_have_value("")
                await expect(literal2).to_have_value("Field label")
                await expect(translation2).to_have_value("")

                # enter translations and save
                await translation2.fill("Veldlabel")
                await page.get_by_role("button", name="Opslaan").click()

            with phase("Select component checks"):
                await page.get_by_text("Field 2").hover()
                # formio doesn't have accessible roles here, so use CSS selector
                await page.locator('css=[ref="editComponent"]').locator(
                    "visible=true"
                ).click()

                # check that the modal is open now
                await expect(page.locator("css=.formio-dialog-content")).to_have_count(
                    1
                )

                # find and click translations tab
                await page.get_by_role("link", name="Vertalingen").click()

                expected_literals = ["Field 2", "Description 2", "Option 1", "Option 2"]
                for index, literal in enumerate(expected_literals):
                    with self.subTest(literal=literal, index=index):
                        literal_loc = page.locator(
                            f'css=[name="data[openForms.translations.nl][{index}]"]'
                        )
                        await expect(literal_loc).to_have_value(literal)

                await page.get_by_role("button", name="Annuleren").click()
                await expect(page.locator("css=.formio-dialog-content")).to_have_count(
                    0
                )

            with phase("save form changes to backend"):
                await page.get_by_role("button", name="Save", exact=True).click()
                changelist_url = str(
                    furl(self.live_server_url) / reverse("admin:forms_form_changelist")
                )
                await expect(page).to_have_url(changelist_url)

        @sync_to_async
        def assertState():
            translations = (
                form.formstep_set.get().form_definition.component_translations
            )
            self.assertEqual(
                translations,
                {
                    "nl": {"Field label": "Veldlabel"},
                    "en": {},
                },
            )

        await assertState()

    async def test_regex_validation_key(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "someField",
                            "label": "Some Field",
                        }
                    ],
                },
            )
            return form

        await create_superuser()
        form = await setUpTestData()
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await page.get_by_role("tab", name="Steps and fields").click()

            # Open the edit modal
            await page.get_by_text("Some Field").hover()
            await page.locator('css=[ref="editComponent"]').locator(
                "visible=true"
            ).click()
            await expect(page.locator("css=.formio-dialog-content")).to_have_count(1)

            # fill the component key field with an invalid value to trigger validation
            key_input = page.get_by_label("Eigenschapnaam")
            await key_input.click()
            await key_input.fill(" +?!")
            parent = key_input.locator("xpath=../..")
            await expect(parent).to_have_class(re.compile(r"has-error"))
            await expect(parent).to_have_class(re.compile(r"has-message"))
            error_message = (
                "De eigenschapsnaam mag alleen alfanumerieke tekens, "
                "onderstrepingstekens, punten en streepjes bevatten en mag niet "
                "worden afgesloten met een streepje of punt."
            )
            await expect(parent).to_contain_text(error_message)
