import re
from contextlib import contextmanager

from django.test import tag
from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import Page, expect

from openforms.config.models import GlobalConfiguration
from openforms.products.tests.factories import ProductFactory
from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser
from openforms.utils.tests.cache import clear_caches
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..factories import (
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
)


@contextmanager
def phase(desc: str):
    yield


async def add_new_step(page: Page):
    await page.get_by_role("tab", name="Steps and fields").click()
    await page.get_by_role("button", name="Add step").click()
    await page.get_by_role("button", name="Create a new form definition").click()


async def drag_and_drop_component(page: Page, component: str):
    await page.get_by_text(component, exact=True).hover()
    await page.mouse.down()
    # This is added to make it work for when there is already a component in the container.
    # Idea taken from: https://playwright.dev/python/docs/input#dragging-manually
    # It says:
    # "If your page relies on the dragover event being dispatched, you need at least two mouse moves to trigger it in
    # all browsers. To reliably issue the second mouse move, repeat your mouse.move() or locator.hover() twice."
    # ... but repeating the hover didn't work. Hence, the extra move.
    await page.mouse.move(0, 0)
    await page.locator('css=[ref="-container"]').hover()
    await page.mouse.up()


async def open_component_options_modal(page: Page, label: str, exact: bool = False):
    """
    Find the component in the builder with the given label and click the edit icon
    to bring up the options modal.
    """
    # hover over component to bring up action icons
    await page.get_by_text(label, exact=exact).hover()
    # formio doesn't have accessible roles here, so use CSS selector
    await page.locator('css=[ref="editComponent"]').locator("visible=true").last.click()
    # check that the modal is open now
    await expect(page.locator("css=.formio-dialog-content")).to_be_visible()


class FormDesignerComponentTranslationTests(E2ETestCase):
    # TODO: once the form builder has been replaced completely with our react-based
    # implemenation, these shims need to be removed.
    translation_map = {}
    translations_data_path = "data[openForms.translations.{locale}]"
    translations_literal_suffix = ""
    translations_translation_suffix = "[translation]"
    is_translations_order_fixed = False

    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)
        config = GlobalConfiguration.get_solo()
        assert isinstance(config, GlobalConfiguration)
        config.enable_react_formio_builder = False
        config.save()

    def _translate(self, text: str) -> str:
        return self.translation_map.get(text, text)

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
                            "tooltip": "Tooltip 1",
                        },
                        {
                            "type": "select",
                            "key": "field2",
                            "label": "Field 2",
                            "description": "Description 2",
                            "tooltip": "Tooltip 2",
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
                await open_component_options_modal(page, "Field 1")

                # find and click translations tab
                await page.get_by_role(
                    "link", name=self._translate("Vertalingen")
                ).click()

                _translations_data_path = self.translations_data_path.format(
                    locale="nl"
                )
                # check the values of the translation inputs
                literal1 = page.locator(f'css=[name="{_translations_data_path}[0]"]')
                translation1 = page.locator(
                    f'css=[name="{_translations_data_path}[0][translation]"]'
                )
                literal2 = page.locator(f'css=[name="{_translations_data_path}[1]"]')
                translation2 = page.locator(
                    f'css=[name="{_translations_data_path}[1][translation]"]'
                )
                literal3 = page.locator(f'css=[name="{_translations_data_path}[2]"]')
                translation3 = page.locator(
                    f'css=[name="{_translations_data_path}[2][translation]"]'
                )

                await expect(literal1).to_have_value("Field 1")
                await expect(translation1).to_have_value("")
                await expect(literal2).to_have_value("Description 1")
                await expect(translation2).to_have_value("")
                await expect(literal3).to_have_value("Tooltip 1")
                await expect(translation3).to_have_value("")

                # edit textfield label literal
                await page.get_by_role("link", name=self._translate("Basis")).click()
                await page.get_by_label("Label").fill("Field label")

                # translations tab needs to be updated - note that the react-base builder
                # preserves the order of literals/translations
                await page.get_by_role(
                    "link", name=self._translate("Vertalingen")
                ).click()

                label_literal = literal3
                label_translation = translation3
                description_literal = literal1
                description_translation = translation1
                tooltip_literal = literal2
                tooltip_translation = translation2

                await expect(label_literal).to_have_value("Field label")
                await expect(label_translation).to_have_value("")
                await expect(description_literal).to_have_value("Description 1")
                await expect(description_translation).to_have_value("")
                await expect(tooltip_literal).to_have_value("Tooltip 1")
                await expect(tooltip_translation).to_have_value("")

                # enter translations and save
                await label_translation.fill("Veldlabel")
                modal = page.locator("css=.formio-dialog-content")
                await modal.get_by_role(
                    "button", name=self._translate("Opslaan"), exact=True
                ).click()

            with phase("Select component checks"):
                await open_component_options_modal(page, "Field 2")
                # find and click translations tab
                await page.get_by_role("link", name="Vertalingen").click()

                expected_literals = [
                    "Field 2",
                    "Description 2",
                    "Tooltip 2",
                    "Option 1",
                    "Option 2",
                ]
                for index, literal in enumerate(expected_literals):
                    with self.subTest(literal=literal, index=index):
                        literal_loc = page.locator(
                            f'css=[name="data[openForms.translations.nl][{index}]"]'
                        )
                        await expect(literal_loc).to_have_value(literal)

                await page.get_by_role("button", name="Cancel").click()
                await expect(page.locator("css=.formio-dialog-content")).to_be_hidden()

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

    @tag("gh-2800")
    async def test_editing_translatable_properties_remembers_translations(self):
        """
        Assert that entering translations and then changing the source string keeps the translation.
        """
        await create_superuser()
        admin_url = str(furl(self.live_server_url) / reverse("admin:forms_form_add"))

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await add_new_step(page)
            await drag_and_drop_component(page, "Tekstveld")
            await expect(page.locator("css=.formio-dialog-content")).to_be_visible()
            label_locator = page.get_by_label("Label", exact=True)
            await label_locator.clear()
            await label_locator.fill("Test")

            # Set an initial translation
            await page.get_by_role("link", name=self._translate("Vertalingen")).click()

            _translations_data_path = self.translations_data_path.format(locale="nl")

            literal = page.locator(
                f'css=[name="{_translations_data_path}[0]{self.translations_literal_suffix}"]'
            )
            translation = page.locator(
                f'css=[name="{_translations_data_path}[0]{self.translations_translation_suffix}"]'
            )
            await expect(literal).to_have_value("Test")
            await expect(translation).to_have_value("")

            await translation.click()
            await translation.fill("Vertaald label")

            # Now change the source string & check the translations are still in place
            await page.get_by_role("link", name=self._translate("Basis")).click()
            await page.get_by_label("Label", exact=True).fill("Test 2")

            await page.get_by_role("link", name=self._translate("Vertalingen")).click()
            await expect(literal).to_have_value("Test 2")
            await expect(translation).to_have_value("Vertaald label")

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
            await open_component_options_modal(page, "Some Field")

            # fill the component key field with an invalid value to trigger validation
            key_input = page.get_by_label(self._translate("Eigenschapnaam"))
            await key_input.click()
            await key_input.fill(" +?!")
            await key_input.blur()
            parent = key_input.locator("xpath=../..")
            await expect(parent).to_have_class(re.compile(r"has-error"))
            # await expect(parent).to_have_class(re.compile(r"has-message"))
            error_message = self._translate(
                "De eigenschapsnaam mag alleen alfanumerieke tekens, "
                "onderstrepingstekens, punten en streepjes bevatten en mag niet "
                "worden afgesloten met een streepje of punt."
            )
            await expect(parent).to_contain_text(error_message)

    async def test_key_automatically_updated_for_files(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [],
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

            # Drag and drop a component
            await drag_and_drop_component(page, "Bestandsupload")

            # Check that the modal is open
            await expect(page.locator("css=.formio-dialog-content")).to_be_visible()

            # Check the key before modifying the label
            key_input = page.get_by_label(self._translate("Eigenschapnaam"))
            await expect(key_input).to_have_value(self._translate("file"))

            # Modify the component label
            label_input = page.get_by_label("Label")
            await label_input.click()
            await label_input.fill("Test")

            # Test that the key also changed
            await expect(key_input).to_have_value("test")

            # Check file name mentions templating
            await page.get_by_role("link", name=self._translate("Bestand")).click()
            await expect(
                page.locator("label").filter(
                    has_text=self._translate("Bestandsnaamsjabloon")
                )
            ).to_be_visible()

    async def test_key_unique_across_steps(self):
        @sync_to_async
        def setUpTestData():
            # set up a form with 2 steps
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="First step",
                formstep__form_definition__configuration={
                    "components": [{"key": "textField", "type": "textfield"}],
                },
            )
            form_def = FormDefinitionFactory.create(
                name_nl="Second step",
                configuration={
                    "components": [],
                },
            )
            FormStepFactory.create(form=form, form_definition=form_def)
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

            # Go to the second form step
            await page.get_by_text("Second step").click()
            await drag_and_drop_component(page, "Tekstveld")

            # Check that the modal is open
            await expect(page.locator("css=.formio-dialog-content")).to_be_visible()

            # Check that the key has been made unique (textField1 vs textField)
            key_input = page.get_by_label(self._translate("Eigenschapnaam"))
            await expect(key_input).to_have_value("textField1")

    @tag("gh-2805")
    async def test_enable_translations_and_create_new_step(self):
        await create_superuser()
        admin_url = str(furl(self.live_server_url) / reverse("admin:forms_form_add"))

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))

            # missing translations warning may not crash the form builder
            await page.get_by_label("Translation enabled").check()
            # there should be a warning displayed about missing translations
            await expect(
                page.get_by_text(
                    re.compile(
                        r"Form has translation enabled, but is missing [0-9]+ translations"
                    )
                )
            ).to_be_visible()

            await add_new_step(page)
            await page.get_by_text("Verouderd").click()
            await drag_and_drop_component(page, "Wachtwoord")
            # save with the defaults
            modal = page.locator("css=.formio-dialog-content")
            await modal.get_by_role(
                "button", name=self._translate("Opslaan"), exact=True
            ).click()

            # the modal should close
            await expect(modal).to_be_hidden()

    @tag("gh-2800")
    async def test_key_automatically_generated_for_select_options(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [],
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

            # Drag and drop a component
            await drag_and_drop_component(page, "Keuzelijst")

            # Check that the modal is open
            await expect(page.locator("css=.formio-dialog-content")).to_be_visible()

            # Update the label
            value_label_input = page.locator('css=[name="data[data.values][0][label]"]')
            await value_label_input.click()
            await value_label_input.fill("Test")

            # Check that the key has been updated
            value_key_input = page.locator('css=[name="data[data.values][0][value]"]')
            await expect(value_key_input).to_have_value("test")

    @tag("gh-2820")
    async def test_editing_content_translations_are_saved(self):
        """
        Assert that entering translations and then changing the source string keeps the translation.
        """
        await create_superuser()
        admin_url = str(furl(self.live_server_url) / reverse("admin:forms_form_add"))

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await add_new_step(page)

            # Open the menu for the layout components
            await page.get_by_text("Opmaak").click()
            await drag_and_drop_component(page, "Vrije tekst")

            await expect(page.locator("css=.formio-dialog-content")).to_be_visible()

            default_string = page.locator("css=.ck-editor__editable").nth(0)
            await default_string.click()
            await default_string.fill("This is the default")

            dutch_translation = page.locator("css=.ck-editor__editable").nth(1)
            await dutch_translation.click()
            await expect(dutch_translation).to_be_focused()
            await dutch_translation.fill("This is the translation")

            await expect(dutch_translation).to_contain_text("This is the translation")

            # Save the component
            await page.get_by_role("button", name="Opslaan").click()

            await open_component_options_modal(page, "This is the default")
            dutch_translation = page.locator("css=.ck-editor__editable").nth(1)

            await expect(dutch_translation).to_contain_text("This is the translation")


class NewFormBuilderFormDesignerComponentTranslationTests(
    FormDesignerComponentTranslationTests
):
    """
    Run all the same tests as FormDesignerComponentTranslationTests, except with the
    new React based form builder enabled.

    # TODO: once the form builder has been replaced completely with our react-based
    # implemenation, this entire subclass has no right to exist anymore -> remove it
    """

    # required because the react based builder takes into account the browser locale,
    # while the form.io builder is hardcoded to NL
    translation_map = {
        "Eigenschapnaam": "Property Name",
        "Basis": "Basic",
        "Vertalingen": "Translations",
        "Opslaan": "Save",
        "Annuleren": "Cancel",
        (
            "De eigenschapsnaam mag alleen alfanumerieke tekens, "
            "onderstrepingstekens, punten en streepjes bevatten en mag niet "
            "worden afgesloten met een streepje of punt."
        ): (
            "The property name must only contain alphanumeric characters, underscores, "
            "dots and dashes and should not be ended by dash or dot."
        ),
        "file": "fileUpload",  # label is File Upload -> derived key is fileUpload
        "Bestand": "File",
        "Bestandsnaamsjabloon": "File name template",
    }
    translations_data_path = "openForms.translations.{locale}"
    translations_literal_suffix = ".literal"
    translations_translation_suffix = ".translation"
    is_translations_order_fixed = True

    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)
        config = GlobalConfiguration.get_solo()
        assert isinstance(config, GlobalConfiguration)
        config.enable_react_formio_builder = True
        config.save()

    @staticmethod
    async def _check_translation(
        page: Page,
        prop: str,
        label: str,
        expected_literal: str,
        expected_translation: str,
    ):
        # there's no built in get_by_description :(
        label_id = await page.get_by_text(label, exact=True).get_attribute("id")
        literal_ = page.locator(f'css=[aria-describedby="{label_id}"]')
        await expect(literal_).to_have_text(expected_literal)
        translation_field = page.get_by_label(f'Translation for "{prop}"', exact=True)
        await expect(translation_field).to_have_value(expected_translation)
        return translation_field

    async def test_editing_translatable_properties(self):
        # completely overridden instead of sharing the test with the old builder - the
        # test code became unmaintainable

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
                            "tooltip": "Tooltip 1",
                        },
                        {
                            "type": "select",
                            "key": "field2",
                            "label": "Field 2",
                            "description": "Description 2",
                            "tooltip": "Tooltip 2",
                            "openForms": {
                                "dataSrc": "manual",
                            },
                            "data": {
                                "values": [
                                    {
                                        "value": "option1",
                                        "label": "Option 1",
                                        "openForms": {
                                            "translations": {
                                                "nl": {
                                                    "label": "Optie 1",
                                                }
                                            }
                                        },
                                    },
                                    {
                                        "value": "option2",
                                        "label": "Option 2",
                                    },
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
                await open_component_options_modal(page, "Field 1")

                # find and click translations tab
                await page.get_by_role(
                    "link", name=self._translate("Vertalingen")
                ).click()

                # check the values of the translation inputs
                await self._check_translation(page, "label", "Label", "Field 1", "")
                await self._check_translation(
                    page, "description", "Description", "Description 1", ""
                )
                await self._check_translation(
                    page, "tooltip", "Tooltip", "Tooltip 1", ""
                )

                # edit textfield label literal
                await page.get_by_role("link", name=self._translate("Basis")).click()
                await page.get_by_label("Label").fill("Field label")

                # translations tab needs to be updated - note that the react-base builder
                # preserves the order of literals/translations
                await page.get_by_role(
                    "link", name=self._translate("Vertalingen")
                ).click()

                # React-based form builder has a more accessible translations table
                label_translation = await self._check_translation(
                    page, "label", "Label", "Field label", ""
                )
                await self._check_translation(
                    page, "description", "Description", "Description 1", ""
                )
                await self._check_translation(
                    page, "tooltip", "Tooltip", "Tooltip 1", ""
                )

                # enter translations and save
                await label_translation.fill("Veldlabel")
                modal = page.locator("css=.formio-dialog-content")
                await modal.get_by_role(
                    "button", name=self._translate("Opslaan"), exact=True
                ).click()

            # TODO: this still uses the old translation mechanism, will follow in a later
            # version of @open-formulieren/formio-builder npm package.
            with phase("Select component checks"):
                await open_component_options_modal(page, "Field 2")

                # find and click translations tab
                await page.get_by_role(
                    "link", name=self._translate("Vertalingen")
                ).click()

                # check the values of the translation inputs
                await self._check_translation(page, "label", "Label", "Field 2", "")
                await self._check_translation(
                    page, "description", "Description", "Description 2", ""
                )
                await self._check_translation(
                    page, "tooltip", "Tooltip", "Tooltip 2", ""
                )

                # Check options translations are present
                option1_translation_field = page.get_by_label(
                    'Translation for option with value "option1"', exact=True
                )
                await expect(option1_translation_field).to_have_value("Optie 1")
                option2_translation_field = page.get_by_label(
                    'Translation for option with value "option2"', exact=True
                )
                await expect(option2_translation_field).to_have_value("")

                await page.get_by_role("button", name="Cancel").click()
                await expect(page.locator("css=.formio-dialog-content")).to_be_hidden()

            with phase("save form changes to backend"):
                await page.get_by_role("button", name="Save", exact=True).click()
                changelist_url = str(
                    furl(self.live_server_url) / reverse("admin:forms_form_changelist")
                )
                await expect(page).to_have_url(changelist_url)

        @sync_to_async
        def assertState():
            fd = form.formstep_set.get().form_definition
            textfield = fd.configuration["components"][0]

            self.assertEqual(
                textfield["openForms"]["translations"]["nl"]["label"],
                "Veldlabel",
            )
            self.assertEqual(fd.component_translations, {})

        await assertState()

    @tag("gh-2800")
    async def test_editing_translatable_properties_remembers_translations(self):
        """
        Assert that entering translations and then changing the source string keeps the translation.
        """
        await create_superuser()
        admin_url = str(furl(self.live_server_url) / reverse("admin:forms_form_add"))

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await add_new_step(page)
            await drag_and_drop_component(page, "Tekstveld")
            await expect(page.locator("css=.formio-dialog-content")).to_be_visible()
            label_locator = page.get_by_label("Label", exact=True)
            await label_locator.clear()
            await label_locator.fill("Test")

            # Set an initial translation
            await page.get_by_role("link", name=self._translate("Vertalingen")).click()

            translation = await self._check_translation(
                page, "label", "Label", expected_literal="Test", expected_translation=""
            )
            await translation.click()
            await translation.fill("Vertaald label")

            # Now change the source string & check the translations are still in place
            await page.get_by_role("link", name=self._translate("Basis")).click()
            await page.get_by_label("Label", exact=True).fill("Test 2")

            await page.get_by_role("link", name=self._translate("Vertalingen")).click()
            await self._check_translation(
                page,
                "label",
                "Label",
                expected_literal="Test 2",
                expected_translation="Vertaald label",
            )

    @tag("gh-2820")
    async def test_editing_content_translations_are_saved(self):
        """
        Assert that entering translations and then changing the source string keeps the translation.
        """
        await create_superuser()
        admin_url = str(furl(self.live_server_url) / reverse("admin:forms_form_add"))

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await add_new_step(page)

            # Open the menu for the layout components
            await page.get_by_text("Opmaak").click()
            await drag_and_drop_component(page, "Vrije tekst")

            await expect(page.locator("css=.formio-dialog-content")).to_be_visible()

            # first translation tab (NL) is the default
            await page.get_by_role("link", name="NL", exact=True).click()
            wysiwyg_nl = page.get_by_label("Editor editing area: main")
            await expect(wysiwyg_nl).to_be_editable()

            await wysiwyg_nl.click()
            await wysiwyg_nl.fill("This is the default/NL translation.")

            await page.get_by_role("link", name="EN", exact=True).click()
            wysiwyg_en = page.get_by_label("Editor editing area: main")
            await expect(wysiwyg_en).to_be_editable()
            await wysiwyg_en.click()
            await wysiwyg_en.fill("This is the English translation.")

            # Save the component
            modal = page.locator("css=.formio-dialog-content")
            await modal.get_by_role("button", name="Save", exact=True).click()

            await open_component_options_modal(
                page, "This is the default/NL translation."
            )

            await page.get_by_role("link", name="NL", exact=True).click()
            wysiwyg_nl_2 = page.get_by_label("Editor editing area: main")
            await expect(wysiwyg_nl_2).to_contain_text(
                "This is the default/NL translation."
            )

            await page.get_by_role("link", name="EN", exact=True).click()
            wysiwyg_en_2 = page.get_by_label("Editor editing area: main")
            await expect(wysiwyg_en_2).to_contain_text(
                "This is the English translation."
            )

    @tag("gh-2800")
    async def test_key_automatically_generated_for_select_options(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [],
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

            # Drag and drop a component
            await drag_and_drop_component(page, "Keuzelijst")

            # Check that the modal is open
            await expect(page.locator("css=.formio-dialog-content")).to_be_visible()

            # Update the label
            value_label_input = page.get_by_label("Option label")
            await value_label_input.click()
            await value_label_input.fill("Test")

            # Check that the key has been updated
            value_key_input = page.get_by_label("Option value")
            await expect(value_key_input).to_have_value("test")


class FormDesignerRegressionTests(E2ETestCase):
    async def test_user_defined_variable_boolean_initial_value_false(self):
        """
        Regression test for https://github.com/open-formulieren/open-forms/issues/2636
        """

        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                formstep__form_definition__name_nl="Playwright test",
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
            await page.get_by_role("tab", name="Variables").click()
            await page.get_by_role("tab", name="User defined").click()
            with phase("Add variable"):
                await page.get_by_text("Add variable").click()
                await page.locator("#id_name").fill("Foo")
                await page.locator("#id_name").blur()
                await page.locator("#id_dataType").select_option(label="Boolean")
                await page.locator("[name='initialValue']").select_option(label="No")

                # Verify that the select updated to the selected value
                await expect(page.locator("[name='initialValue']")).to_have_value(
                    "false"
                )

            with phase("Save variable and check state"):
                await page.get_by_text("Save and continue editing").click()
                await page.get_by_role("tab", name="Variables").click()
                await page.get_by_role("tab", name="User defined").click()

                # Verify that the select still holds the correct value
                await expect(page.locator("[name='initialValue']")).to_have_value(
                    "false"
                )

        @sync_to_async
        def assertState():
            user_defined_vars = form.formvariable_set.filter(
                source=FormVariableSources.user_defined
            )

            self.assertEqual(user_defined_vars.count(), 1)

            created_var = user_defined_vars.first()

            self.assertEqual(created_var.data_type, FormVariableDataTypes.boolean)
            self.assertEqual(created_var.initial_value, False)

        await assertState()

    async def test_user_defined_variable_boolean_initial_value_true(self):
        """
        Regression test for https://github.com/open-formulieren/open-forms/issues/2636
        """

        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                formstep__form_definition__name_nl="Playwright test",
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
            await page.get_by_role("tab", name="Variables").click()
            await page.get_by_role("tab", name="User defined").click()
            with phase("Add variable"):
                await page.get_by_text("Add variable").click()
                await page.locator("#id_name").fill("Foo")
                await page.locator("#id_name").blur()
                await page.locator("#id_dataType").select_option(label="Boolean")
                await page.locator("[name='initialValue']").select_option(label="Yes")

                # Verify that the select updated to the selected value
                await expect(page.locator("[name='initialValue']")).to_have_value(
                    "true"
                )

            with phase("Save variable and check state"):
                await page.get_by_text("Save and continue editing").click()
                await page.get_by_role("tab", name="Variables").click()
                await page.get_by_role("tab", name="User defined").click()

                # Verify that the select still holds the correct value
                await expect(page.locator("[name='initialValue']")).to_have_value(
                    "true"
                )

        @sync_to_async
        def assertState():
            user_defined_vars = form.formvariable_set.filter(
                source=FormVariableSources.user_defined
            )

            self.assertEqual(user_defined_vars.count(), 1)

            created_var = user_defined_vars.first()

            self.assertEqual(created_var.data_type, FormVariableDataTypes.boolean)
            self.assertEqual(created_var.initial_value, True)

        await assertState()

    async def test_logic_rule_trigger_from_step_show_saved_value_in_select(self):
        """
        Regression test for https://github.com/open-formulieren/open-forms/issues/2636
        """

        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
            )
            return form

        await create_superuser()
        form = await setUpTestData()

        @sync_to_async
        def get_formstep_uuid():
            return str(form.formstep_set.first().uuid)

        formstep_uuid = await get_formstep_uuid()

        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await page.get_by_role("tab", name="Logic").click()

            with phase("Add logic rule with triggerFromStep"):
                await page.get_by_text("Add rule").click()
                await page.get_by_text("Advanced").click()
                await page.get_by_title("Advanced options").click()
                await page.locator("[name='triggerFromStep']").select_option(
                    label="Playwright test"
                )
                await page.locator("[name='jsonLogicTrigger']").fill('{"==": [1, 1]}')

            with phase("Save logic rule and check state"):
                await page.get_by_text("Save and continue editing").click()
                await page.get_by_role("tab", name="Logic").click()
                await page.get_by_title("Advanced options").click()

                # Verify that the select still holds the correct value
                await expect(page.locator("[name='triggerFromStep']")).to_have_value(
                    formstep_uuid
                )

        @sync_to_async
        def assertState():
            form_logic = form.formlogic_set

            self.assertEqual(form_logic.count(), 1)

            created_form_logic = form_logic.first()

            self.assertEqual(
                created_form_logic.trigger_from_step, form.formstep_set.first()
            )

        await assertState()

    @tag("gh-2769")
    async def test_max_min_date_validation(self):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "datetime",
                            "key": "field1",
                            "label": "Some Field",
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
            # Goto "Steps and fields"
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await page.get_by_role("tab", name="Steps and fields").click()

            with phase("Initial set up of datetime validation"):
                await open_component_options_modal(page, "Some Field")
                await page.get_by_role("link", name="Validatie").click()

                # select the validation mode in the dropdown
                label = page.get_by_text("Validatiemethode", exact=True).first
                field = label.locator("..")  # grab the parent
                dropdown = field.get_by_role("combobox")
                await dropdown.click()
                await dropdown.get_by_text("Ten opzichte van een variabele").click()

                # Fill in years, months, days and submit
                years = page.get_by_label("Jaren")
                months = page.get_by_label("Maanden")
                days = page.get_by_label("Dagen")
                await years.fill("1")
                await months.fill("1")
                await days.fill("1")
                await page.get_by_role("button", name="Opslaan").click()

                # Navigate back to Validation
                await open_component_options_modal(page, "Some Field")
                await page.get_by_role("link", name="Validatie").click()

                # Check expectations
                await expect(years).to_have_value("1")
                await expect(months).to_have_value("1")
                await expect(months).to_have_value("1")

                await page.get_by_role("button", name="Opslaan").click()

            with phase("Change values for datetime validation"):
                await open_component_options_modal(page, "Some Field")
                await page.get_by_role("link", name="Validatie").click()

                # Fill in years, months, days and submit
                years = page.get_by_label("Jaren")
                months = page.get_by_label("Maanden")
                days = page.get_by_label("Dagen")
                await years.fill("8")
                await months.fill("8")
                await days.fill("8")
                await page.get_by_role("button", name="Opslaan").click()

                # Navigate back to Validation
                await open_component_options_modal(page, "Some Field")
                await page.get_by_role("link", name="Validatie").click()

                # Check expectations
                await expect(years).to_have_value("8")
                await expect(months).to_have_value("8")
                await expect(months).to_have_value("8")

                # close modal again
                await page.get_by_role("button", name="Cancel").click()

            with phase("save form changes to backend"):
                await page.get_by_role("button", name="Save", exact=True).click()
                changelist_url = str(
                    furl(self.live_server_url) / reverse("admin:forms_form_changelist")
                )
                await expect(page).to_have_url(changelist_url)

        @sync_to_async
        def assertState():
            configuration = form.formstep_set.get().form_definition.configuration
            component = configuration["components"][0]
            self.assertEqual(component["key"], "field1")
            self.assertEqual(
                component["openForms"]["minDate"],
                {
                    "mode": "relativeToVariable",
                    "variable": "now",
                    "includeToday": None,
                    "operator": "add",
                    "delta": {
                        "years": 8,
                        "months": 8,
                        "days": 8,
                    },
                },
            )

        await assertState()

    @tag("gh-2821")
    async def test_map_component_edit_properties(self):
        await create_superuser()
        admin_url = str(furl(self.live_server_url) / reverse("admin:forms_form_add"))

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await add_new_step(page)
            await page.get_by_role("button", name="Speciale velden").click()
            await drag_and_drop_component(page, "Kaart")

            await expect(page.locator("css=.formio-dialog-content")).to_be_visible()
            await expect(page.get_by_label("Label")).to_be_visible()

    @tag("gh-2945")
    async def test_creating_user_defined_variables_doesnt_wrongly_update_logic(self):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "textfield",
                            "label": "Some Field",
                        },
                    ],
                },
            )
            FormLogicFactory.create(
                form=form,
                json_logic_trigger={"==": [{"var": "textfield"}, "test"]},
                actions=[],
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

            with phase("Create a user defined variable"):
                await page.get_by_role("tab", name="Variables").click()
                await page.get_by_role("tab", name="User defined").click()
                await page.get_by_role("button", name="Add variable").click()
                await page.locator("css=[name=name]").fill("Foo")

            with phase("Check logic rule is not broken"):
                await page.get_by_role("tab", name="Logic").click()

                # If the operand is still visible, the logic rule has not changed
                await expect(page.locator("css=[name=operand]")).to_be_visible()

    @tag("gh-2947")
    async def test_number_components_have_custom_error_fields(self):
        @sync_to_async
        def setUpTestData():
            return FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "number",
                            "key": "numberField",
                            "label": "Number Field",
                        },
                    ],
                },
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

            # Go to the validation tab of the number component
            await page.get_by_role("tab", name="Steps and fields").click()
            await open_component_options_modal(page, "Number Field")
            await page.get_by_role("link", name="Validatie").click()

            # Check the custom errors for the number component
            await page.get_by_text("Foutmeldingen").click()
            await expect(
                page.locator(
                    'css=[name="data[translations][translatedErrors.nl][0][__key]"]'
                )
            ).to_be_visible()
            await expect(
                page.locator(
                    'css=[name="data[translations][translatedErrors.nl][0][__key]"]'
                )
            ).to_have_value("required")
            await expect(
                page.locator(
                    'css=[name="data[translations][translatedErrors.nl][1][__key]"]'
                )
            ).to_be_visible()
            await expect(
                page.locator(
                    'css=[name="data[translations][translatedErrors.nl][1][__key]"]'
                )
            ).to_have_value("min")
            await expect(
                page.locator(
                    'css=[name="data[translations][translatedErrors.nl][2][__key]"]'
                )
            ).to_be_visible()
            await expect(
                page.locator(
                    'css=[name="data[translations][translatedErrors.nl][2][__key]"]'
                )
            ).to_have_value("max")

    @tag("gh-3132")
    async def test_replacing_step_with_overlapping_config(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                name_nl="Playwright test",
            )
            fd1 = FormDefinitionFactory.create(
                name="Form definition 1",
                slug="form-definition-1",
                configuration={
                    "components": [{"key": "textfield", "type": "textfield"}]
                },
            )
            FormStepFactory.create(form=form, form_definition=fd1)

            # Not yet related
            FormDefinitionFactory.create(
                name="Form definition 2",
                slug="form-definition-2",
                is_reusable=True,
                configuration={
                    "components": [{"key": "textfield", "type": "textfield"}]
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
            await page.get_by_role("button", name="Add step").click()

            # Add form definition with overlapping key names
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.get_by_role(
                "combobox", name="Select form definition"
            ).select_option(label="Form definition 2")
            await page.get_by_role("button", name="Confirm").click()

            # Delete initial form definition
            page.on("dialog", lambda dialog: dialog.accept())
            sidebar = page.locator("css=.edit-panel__nav").get_by_role("list")
            bin_icon = sidebar.get_by_role("listitem").nth(0).get_by_title("Delete")
            await bin_icon.click()

            await expect(page.get_by_text("Form definition 1")).not_to_be_visible()

            # Save form
            await page.locator('[name="_save"]', has_text="Save").click()

            await page.get_by_role("tab", name="Steps and fields").click()

            error_node = page.locator("css=.error")
            await expect(error_node).not_to_be_visible()

    @tag("gh-3422")
    async def test_removing_step_doesnt_break_form(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Form with 2 steps",
            )
            FormStepFactory.create(
                form=form,
                form_definition__configuration={
                    "components": [{"type": "textfield", "key": "textA"}]
                },
            )
            form_step2 = FormStepFactory.create(
                form=form,
                form_definition__configuration={
                    "components": [{"type": "textfield", "key": "textB"}]
                },
            )
            FormLogicFactory.create(form=form, trigger_from_step=form_step2)
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

            # Delete the second step
            page.on("dialog", lambda dialog: dialog.accept())
            sidebar = page.locator("css=.edit-panel__nav").get_by_role("list")
            bin_icon = sidebar.get_by_role("listitem").nth(1).get_by_title("Delete")
            await bin_icon.click()

            await page.get_by_role("tab", name="Logic").click()

            # Check that you can delete the logic rule
            bin_icon = page.get_by_title("Delete").first
            await expect(bin_icon).to_be_visible()

            # Check that a warning is present
            warning = page.get_by_role("listitem").get_by_text(
                "The selected trigger step could not be found in this form! Please change it!"
            )
            await expect(warning).to_be_visible()


class FormDesignerTooltipTests(E2ETestCase):
    async def test_tooltip_fields_are_present(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright tooltip test",
                name_nl="Playwright tooltip test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright tooltip test",
                formstep__form_definition__configuration={
                    "components": [
                        {"type": "bsn", "key": "bsn", "label": "BSN 1"},
                        {"type": "checkbox", "key": "checkbox", "label": "Checkbox 1"},
                        {"type": "currency", "key": "currency", "label": "Currency 1"},
                        {"type": "date", "key": "date", "label": "Date 1"},
                        {
                            "type": "datetime",
                            "key": "dateTime",
                            "label": "Date / Time 1",
                        },
                        {"type": "email", "key": "email", "label": "Email 1"},
                        {"type": "file", "key": "file", "label": "File Upload 1"},
                        {"type": "iban", "key": "iban", "label": "IBAN 1"},
                        {
                            "type": "licenseplate",
                            "key": "licenseplate",
                            "label": "License plate 1",
                            # The intent from the existing code is for this to be baked into the
                            # component definition, and the TypeScript type definitions are set up
                            # accordingly. There is a data migration normalizing existing data
                            # and handling old exports being re-imported.
                            "validate": {
                                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$",
                            },
                        },
                        {"type": "number", "key": "number", "label": "Number 1"},
                        {"type": "password", "key": "password", "label": "Password 1"},
                        {
                            "type": "phoneNumber",
                            "key": "phoneNumber",
                            "label": "Phone Number 1",
                        },
                        {
                            "type": "postcode",
                            "key": "postcode",
                            "label": "Postcode 1",
                            # The intent from the existing code is for this to be baked into the
                            # component definition, and the TypeScript type definitions are set up
                            # accordingly. There is a data migration normalizing existing data
                            # and handling old exports being re-imported.
                            "validate": {
                                "pattern": r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$",
                            },
                        },
                        {
                            "type": "radio",
                            "key": "radio",
                            "label": "Radio 1",
                            "openForms": {"dataSrc": "manual"},
                            "values": [
                                {"value": "option", "label": "Option"},
                            ],
                        },
                        {
                            "type": "select",
                            "key": "select",
                            "label": "Select 1",
                            "openForms": {"dataSrc": "manual"},
                            "dataSrc": "values",
                            "data": {
                                "values": [
                                    {"value": "option", "label": "Option"},
                                ],
                            },
                        },
                        {
                            "type": "selectboxes",
                            "key": "selectBoxes",
                            "label": "Select Boxes 1",
                            "openForms": {"dataSrc": "manual"},
                            "values": [
                                {"value": "option", "label": "Option"},
                            ],
                            "defaultValue": {},
                        },
                        {
                            "type": "signature",
                            "key": "signature",
                            "label": "Signature 1",
                        },
                        {"type": "textarea", "key": "textArea", "label": "Text Area 1"},
                        {"type": "time", "key": "time", "label": "Time 1"},
                        {
                            "type": "fieldset",
                            "key": "fieldset",
                            "label": "Field Set 1",
                            "components": [
                                {
                                    "type": "datagrid",
                                    "key": "datagrid",
                                    "label": "Repeating group",
                                },
                                {
                                    "type": "textfield",
                                    "key": "textField",
                                    "label": "Text Field 1",
                                },
                            ],
                        },
                        {"type": "map", "key": "map", "label": "Map 1"},
                    ]
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

            labels = [
                "BSN 1",
                "Checkbox 1",
                "Currency 1",
                "Date 1",
                "Date / Time 1",
                "Email 1",
                "File Upload 1",
                "IBAN 1",
                "License plate 1",
                "Number 1",
                "Password 1",
                "Phone Number 1",
                "Postcode 1",
                "Radio 1",
                "Select 1",
                "Select Boxes 1",
                "Signature 1",
                "Text Area 1",
                "Text Field 1",
                "Time 1",
                "Map 1",
            ]

            for label in labels:
                with self.subTest(label=label):
                    await open_component_options_modal(page, label, exact=True)
                    await expect(page.get_by_label("Tooltip")).to_be_visible()

                    modal = page.locator("css=.formio-dialog-content")
                    await modal.get_by_role("button", name="Cancel").click()


class FormDesignerMapComponentTests(E2ETestCase):
    async def test_map_component_without_latitude(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright map test",
                generate_minimal_setup=True,
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "map",
                            "key": "map",
                            "label": "Map 1",
                            "lat": 52.1326332,
                            "lng": 5.291266,
                            "defaultZoom": 1,
                            "initialCenter": {"lat": 52.132123, "lng": 12.123123},
                            "useConfigDefaultMapSettings": False,
                        }
                    ]
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

            await open_component_options_modal(page, "Map 1", exact=True)
            # both fields are required so we clear one.
            await page.get_by_label("Latitude").clear()

            await page.get_by_role("button", name="Opslaan").first.click()

            error_node = page.locator("css=.error")
            await expect(error_node).to_be_visible()

    async def test_map_component_without_longitude(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright map test",
                generate_minimal_setup=True,
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "key": "map",
                            "lat": 52.1326332,
                            "lng": 5.291266,
                            "type": "map",
                            "label": "Map 1",
                            "openForms": {},
                            "defaultZoom": 1,
                            "defaultValue": 9,
                            "initialCenter": {"lat": 52.132123, "lng": 12.123123},
                            "useConfigDefaultMapSettings": False,
                        }
                    ]
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

            await open_component_options_modal(page, "Map 1", exact=True)
            # both fields are required so we clear one.
            await page.get_by_label("Longitude").clear()

            await page.get_by_role("button", name="Opslaan").first.click()

            error_node = page.locator("css=.error")
            await expect(error_node).to_be_visible()


class AppointmentFormTests(E2ETestCase):
    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

    async def test_appointment_form_nukes_irrelevant_configuration(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright appointment test",
                generate_minimal_setup=True,
                is_appointment=False,
                product=ProductFactory.create(),
            )
            FormRegistrationBackendFactory.create(
                form=form,
                backend="email",
                options={
                    "to_emails": ["foo@example.com"],
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

            await page.get_by_label("Appointment enabled").click()

            with phase("save form changes to backend"):
                await page.get_by_role("button", name="Save", exact=True).click()
                changelist_url = str(
                    furl(self.live_server_url) / reverse("admin:forms_form_changelist")
                )
                await expect(page).to_have_url(changelist_url)

        @sync_to_async
        def assertState():
            form.refresh_from_db()

            self.assertTrue(form.is_appointment)
            self.assertFalse(form.formstep_set.exists())
            self.assertFalse(form.formvariable_set.exists())
            self.assertFalse(form.registration_backends.exists())
            self.assertEqual(form.payment_backend, "")
            self.assertEqual(form.payment_backend_options, {})
            self.assertIsNone(form.product)

        await assertState()


class SelectReuseableFormDefinitionsTests(E2ETestCase):
    async def test_no_reuseable_form_definition_options_are_available_when_all_part_of_the_form(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright map test",
            )
            form_definition_1 = FormDefinitionFactory.create(
                name="FORM DEFINITION #1",
                configuration={
                    "display": "form",
                },
                is_reusable=True,
            )
            form_definition_2 = FormDefinitionFactory.create(
                name="FORM DEFINITION #2",
                configuration={
                    "display": "form",
                },
                is_reusable=True,
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #3",
                configuration={
                    "display": "form",
                },
                is_reusable=False,
            )
            FormStepFactory.create(form=form, form_definition=form_definition_1)
            FormStepFactory.create(form=form, form_definition=form_definition_2)
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

            # Add step and open selectbox
            await page.get_by_role("button", name="Add step").click()
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.locator("css=#id_form-definition").click()
            selectbox = page.locator("css=#id_form-definition")

            # Check if no options are available in the selectbox
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #1")
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #2")
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #3")

    async def test_all_reuseable_form_definition_options_are_available_when_not_part_of_the_form(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright map test",
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #1",
                configuration={
                    "display": "form",
                },
                is_reusable=True,
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #2",
                configuration={
                    "display": "form",
                },
                is_reusable=True,
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #3",
                configuration={
                    "display": "form",
                },
                is_reusable=False,
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

            # Add step and open selectbox
            await page.get_by_role("button", name="Add step").click()
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.locator("css=#id_form-definition").click()
            selectbox = page.locator("css=#id_form-definition")

            # Check if all reusable for steps are available
            await expect(selectbox).to_contain_text("FORM DEFINITION #1")
            await expect(selectbox).to_contain_text("FORM DEFINITION #2")
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #3")

    async def test_if_reusable_form_definition_is_available_again_after_removing_it_from_the_form(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright map test",
            )
            form_definition_1 = FormDefinitionFactory.create(
                name="FORM DEFINITION #1",
                configuration={
                    "display": "form",
                },
                is_reusable=True,
            )
            form_definition_2 = FormDefinitionFactory.create(
                name="FORM DEFINITION #2",
                configuration={
                    "display": "form",
                },
                is_reusable=True,
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #3",
                configuration={
                    "display": "form",
                },
                is_reusable=False,
            )
            FormStepFactory.create(form=form, form_definition=form_definition_1)
            FormStepFactory.create(form=form, form_definition=form_definition_2)
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

            # Add step and open selectbox
            await page.get_by_role("button", name="Add step").click()
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.locator("css=#id_form-definition").click()
            selectbox = page.locator("css=#id_form-definition")

            # Check if no options are available in the selectbox
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #1")
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #2")
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #3")

            # Close model
            await page.get_by_title("Sluiten").click()

            # Delete the second step
            page.on("dialog", lambda dialog: dialog.accept())
            sidebar = page.locator("css=.edit-panel__nav").get_by_role("list")
            await sidebar.get_by_role("listitem").nth(1).get_by_title("Delete").click()

            # Select third form step and open selectbox
            await sidebar.get_by_role("listitem").nth(1).get_by_text(
                "Stap 3 [new]"
            ).click()
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.locator("css=#id_form-definition").click()
            selectbox = page.locator("css=#id_form-definition")

            # Check if FORM DEFINITION #2 is the only available option
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #1")
            await expect(selectbox).to_contain_text("FORM DEFINITION #2")
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #3")

    async def test_if_reusable_form_definition_is_not_available_after_adding_it_from_the_form(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright map test",
            )
            form_definition_1 = FormDefinitionFactory.create(
                name="FORM DEFINITION #1",
                configuration={
                    "display": "form",
                },
                is_reusable=True,
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #2",
                configuration={
                    "display": "form",
                },
                is_reusable=True,
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #3",
                configuration={
                    "display": "form",
                },
                is_reusable=False,
            )
            FormStepFactory.create(form=form, form_definition=form_definition_1)
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

            # Add step and open selectbox
            await page.get_by_role("button", name="Add step").click()
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.locator("css=#id_form-definition").click()
            selectbox = page.locator("css=#id_form-definition")

            # Check if FORM DEFINITION #2 is the only available option
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #1")
            await expect(selectbox).to_contain_text("FORM DEFINITION #2")
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #3")

            # Select FORM DEFINITION #2 and add it to the form steps
            await selectbox.select_option("FORM DEFINITION #2")
            await page.get_by_role("button", name="Confirm").click()

            # Add step and open select box
            await page.get_by_role("button", name="Add step").click()
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.locator("css=#id_form-definition").click()
            selectbox = page.locator("css=#id_form-definition")

            # Check if no options are available in the selectbox
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #1")
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #2")
            await expect(selectbox).not_to_contain_text("FORM DEFINITION #3")


class FormDesignerDuplicateKeyWarningTests(E2ETestCase):
    async def test_adding_reusable_form_without_duplicate_key_shows_no_warnings(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright duplicate keys test",
            )
            form_definition_1 = FormDefinitionFactory.create(
                name="FORM DEFINITION #1",
                configuration={
                    "display": "form",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "duplicate-key",
                            "label": "Duplicate Key",
                        },
                    ],
                },
                is_reusable=True,
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #2",
                configuration={
                    "display": "form",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "duplicate-key-2",
                            "label": "Duplicate Key 2",
                        }
                    ],
                },
                is_reusable=True,
            )
            FormStepFactory.create(form=form, form_definition=form_definition_1)
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

            # Check if there are no warnings at the start of the test
            await expect(page.locator("css=.messagelist")).not_to_be_visible()

            # Add step and open selectbox
            await page.get_by_role("button", name="Add step").click()
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.locator("css=#id_form-definition").click()
            selectbox = page.locator("css=#id_form-definition")

            # Select FORM DEFINITION #2 and add it to the form steps
            await selectbox.select_option("FORM DEFINITION #2")
            await page.get_by_role("button", name="Confirm").click()

            # Check if there are no warnings on the FORM DEFINITION #2 form step
            await expect(page.locator("css=.messagelist")).not_to_be_visible()

            # Go back to the first form definition
            await page.get_by_role("button", name="FORM DEFINITION #1").click()

            # Check if there still are no warnings on the FORM DEFINITION #1 form step
            await expect(page.locator("css=.messagelist")).not_to_be_visible()

    async def test_adding_reusable_form_with_duplicate_key_shows_warnings(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright duplicate keys test",
            )
            form_definition_1 = FormDefinitionFactory.create(
                name="FORM DEFINITION #1",
                configuration={
                    "display": "form",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "duplicate-key",
                            "label": "Duplicate Key",
                        },
                        {
                            "type": "textfield",
                            "key": "duplicate-key-2",
                            "label": "Duplicate Key 2",
                        },
                    ],
                },
                is_reusable=True,
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #2",
                configuration={
                    "display": "form",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "duplicate-key",
                            "label": "Duplicate Key",
                        }
                    ],
                },
                is_reusable=True,
            )
            FormDefinitionFactory.create(
                name="FORM DEFINITION #3",
                configuration={
                    "display": "form",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "duplicate-key-2",
                            "label": "Duplicate Key 2",
                        }
                    ],
                },
                is_reusable=True,
            )
            FormStepFactory.create(form=form, form_definition=form_definition_1)
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

            # Check if there are no warnings at the start of the test
            await expect(page.locator("css=.messagelist")).not_to_be_visible()

            # Add step and open selectbox
            await page.get_by_role("button", name="Add step").click()
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.locator("css=#id_form-definition").click()
            selectbox = page.locator("css=#id_form-definition")

            # Select FORM DEFINITION #2 and add it to the form steps
            await selectbox.select_option("FORM DEFINITION #2")
            await page.get_by_role("button", name="Confirm").click()

            # Check if the warning message shows up as expected
            await expect(page.locator("css=.messagelist")).to_contain_text(
                "A key is duplicated: "
                'duplicate-key: in "FORM DEFINITION #1" and "FORM DEFINITION #2"'
            )

            # Add step and open selectbox
            await page.get_by_role("button", name="Add step").click()
            await page.get_by_role(
                "button", name="Select existing form definition"
            ).click()
            await page.locator("css=#id_form-definition").click()
            selectbox = page.locator("css=#id_form-definition")

            # Select FORM DEFINITION #3 and add it to the form steps
            await selectbox.select_option("FORM DEFINITION #3")
            await page.get_by_role("button", name="Confirm").click()

            # Check if the warning message shows up as expected
            await expect(page.locator("css=.messagelist")).to_contain_text(
                "A key is duplicated: "
                'duplicate-key-2: in "FORM DEFINITION #1" and "FORM DEFINITION #3"'
            )

            # Go back to the first form definition
            await page.get_by_role("button", name="FORM DEFINITION #1").click()

            # Check if the warning message shows up as expected
            await expect(page.locator("css=.messagelist")).to_contain_text(
                "2 keys are duplicated: "
                'duplicate-key: in "FORM DEFINITION #1" and "FORM DEFINITION #2"'
                'duplicate-key-2: in "FORM DEFINITION #1" and "FORM DEFINITION #3"'
            )
