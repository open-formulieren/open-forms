import re

from django.test import tag
from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import Page, expect

from openforms.formio.constants import DataSrcOptions
from openforms.products.tests.factories import ProductFactory
from openforms.tests.e2e.base import (
    E2ETestCase,
    browser_page,
    create_superuser,
    rs_select_option,
)
from openforms.utils.tests.cache import clear_caches
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ...models import Form
from ..factories import (
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
)
from .helpers import (
    click_modal_button,
    close_modal,
    enter_json_in_editor,
    open_component_options_modal,
    phase,
    skip_on_webtest,
)


async def add_new_step(page: Page):
    await page.get_by_role("tab", name="Steps and fields").click()
    await page.get_by_role("button", name="Add step").click()
    await page.get_by_role("button", name="Create a new form definition").click()


async def drag_and_drop_component(
    page: Page, component: str, parent_ref: str = "sidebar-groups"
):
    await (
        page.locator(f'css=[ref="{parent_ref}"]')
        .get_by_text(component, exact=True)
        .hover()
    )
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


class FormDesignerComponentTranslationTests(E2ETestCase):
    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

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
                                "dataSrc": DataSrcOptions.manual,
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
                await page.get_by_role("link", name="Translations").click()

                # check the values of the translation inputs
                await self._check_translation(page, "label", "Label", "Field 1", "")
                await self._check_translation(
                    page, "description", "Description", "Description 1", ""
                )
                await self._check_translation(
                    page, "tooltip", "Tooltip", "Tooltip 1", ""
                )

                # edit textfield label literal
                await page.get_by_role("link", name="Basic").click()
                await page.get_by_label("Label").fill("Field label")

                # translations tab needs to be updated - note that the react-base builder
                # preserves the order of literals/translations
                await page.get_by_role("link", name="Translations").click()

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
                await close_modal(page, "Save", exact=True)

            # TODO: this still uses the old translation mechanism, will follow in a later
            # version of @open-formulieren/formio-builder npm package.
            with phase("Select component checks"):
                await open_component_options_modal(page, "Field 2")

                # find and click translations tab
                await page.get_by_role("link", name="Translations").click()

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
            await page.get_by_role("link", name="Translations").click()

            translation = await self._check_translation(
                page, "label", "Label", expected_literal="Test", expected_translation=""
            )
            await translation.click()
            await translation.fill("Vertaald label")

            # Now change the source string & check the translations are still in place
            await page.get_by_role("link", name="Basic").click()
            await page.get_by_label("Label", exact=True).fill("Test 2")

            await page.get_by_role("link", name="Translations").click()
            await self._check_translation(
                page,
                "label",
                "Label",
                expected_literal="Test 2",
                expected_translation="Vertaald label",
            )

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
            key_input = page.get_by_label("Property Name")
            await key_input.click()
            await key_input.fill(" +?!")
            await key_input.blur()
            parent = key_input.locator("xpath=../..")
            await expect(parent).to_have_class(re.compile(r"has-error"))
            # await expect(parent).to_have_class(re.compile(r"has-message"))
            error_message = (
                "The property name must only contain alphanumeric characters, "
                "underscores, dots and dashes and should not be ended by dash or dot."
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
            key_input = page.get_by_label("Property Name")
            await expect(key_input).to_have_value("fileUpload")

            # Modify the component label
            label_input = page.get_by_label("Label")
            await label_input.click()
            await label_input.fill("Test")

            # Test that the key also changed
            await expect(key_input).to_have_value("test")

            # Check file name mentions templating
            await page.get_by_role("link", name="File").click()
            await expect(
                page.locator("label").filter(has_text="File name template")
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
            key_input = page.get_by_label("Property Name")
            await expect(key_input).to_have_value("textField1")

    async def test_textfields_default_value_empty_string(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Test textfields default value empty string",
                name_nl="Test textfields default value empty string",
                generate_minimal_setup=False,
            )
            return form

        await create_superuser()
        form = await setUpTestData()
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )
        admin_changelist_url = str(
            furl(self.live_server_url) / reverse("admin:forms_form_changelist")
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))

            with phase("Populate and save form"):
                await add_new_step(page)
                step_name_input = page.get_by_role(
                    "textbox", name="Step name", exact=True
                )
                await step_name_input.click()
                await step_name_input.fill("Step 1")

                basic_components = [
                    "Tekstveld",
                    "E-mail",
                    "Tijd",
                    "Telefoonnummer",
                    "Tekstvlak",
                ]
                for component in basic_components:
                    await drag_and_drop_component(page, component, "group-panel-custom")
                    await close_modal(page, "Save", exact=True)

                basic_components_with_multiple = [
                    "Tekstveld",
                    "E-mail",
                    "Tijd",
                    "Telefoonnummer",
                    "Tekstvlak",
                ]
                for component in basic_components_with_multiple:
                    await drag_and_drop_component(page, component, "group-panel-custom")
                    await page.get_by_label("Multiple values", exact=True).check()
                    await close_modal(page, "Save", exact=True)

                # Open the special fields list
                await page.get_by_role(
                    "button", name="Speciale velden", exact=True
                ).click()

                special_components = ["IBAN", "Kenteken", "Mede-ondertekenen"]
                for component in special_components:
                    await drag_and_drop_component(page, component)
                    await close_modal(page, "Save", exact=True)

                special_components_with_multiple = ["IBAN", "Kenteken"]
                for component in special_components_with_multiple:
                    await drag_and_drop_component(page, component)
                    await page.get_by_label("Multiple values", exact=True).check()
                    await close_modal(page, "Save", exact=True)

                # Save form
                await page.get_by_role("button", name="Save", exact=True).click()
                await page.wait_for_url(admin_changelist_url)

            with phase("Validate default values"):

                @sync_to_async
                def assertFormValues():
                    for component in form.iter_components():
                        expected = [""] if component.get("multiple", False) else ""

                        self.assertEqual(
                            component["defaultValue"],
                            expected,
                            msg=f"Test failed for component {component['key']} with multiple set to {component.get('multiple', False)}",
                        )

                await assertFormValues()

    @tag("dh-5104")
    async def test_radio_component_default_value_empty_string(self):
        @sync_to_async
        def setUpTestData():
            form = FormFactory.create()
            FormStepFactory.create(
                form=form, form_definition__configuration={"components": []}
            )
            return form

        await create_superuser()
        form = await setUpTestData()
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )
        admin_changelist_url = str(
            furl(self.live_server_url) / reverse("admin:forms_form_changelist")
        )

        async with browser_page() as page:
            await self._admin_login(page)

            with phase("Populate and save form"):
                await page.goto(str(admin_url))
                await page.get_by_role("tab", name="Steps and fields").click()

                await drag_and_drop_component(page, "Radio", "group-panel-custom")
                await page.get_by_test_id("input-label").fill("Custom Radio")
                await page.get_by_test_id("input-values[0].label").fill("Label")
                await page.get_by_test_id("input-values[0].value").fill("Value")
                await close_modal(page, "Save")

                # Save form
                await page.get_by_role("button", name="Save", exact=True).click()
                await page.wait_for_url(admin_changelist_url)

            with phase("Validate default value after create"):

                @sync_to_async
                def assertFormValues():
                    configuration = (
                        form.formstep_set.get().form_definition.configuration
                    )
                    radio_component = configuration["components"][0]
                    self.assertEqual(
                        radio_component["defaultValue"],
                        "",
                    )

                await assertFormValues()

            # When creating a radio component, the defaultValue is set correctly in the
            # database.
            #
            # This bug appears in the json view, where the `defaultValue` will show as
            # `null` after `Save and continue editing`.
            # The json view is a conditionally rendered html list of divs
            # (only elements that are directly shown are targetable in the dom)
            #
            # So to test if this bug happens, we just save it again, and then check the
            # database.
            with phase("Edit the form"):
                await page.goto(str(admin_url))
                await page.get_by_role("tab", name="Steps and fields").click()

                # The defaultValue in the bug is set to `null`.
                # If we open the component, and immediately save it, the defaultValue
                # will change from `""` (in the db) to `null` (set by bug)
                await open_component_options_modal(page, "Custom Radio", exact=True)
                await close_modal(page, "Save", exact=True)

                # Save form
                await page.get_by_role("button", name="Save", exact=True).click()
                await page.wait_for_url(admin_changelist_url)

            with phase("Validate default value after editing"):

                @sync_to_async
                def assertFormValues():
                    configuration = (
                        form.formstep_set.get().form_definition.configuration
                    )
                    radio_component = configuration["components"][0]

                    self.assertEqual(
                        radio_component["defaultValue"],
                        "",
                    )

                await assertFormValues()

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
            await page.get_by_text("Speciale velden").click()
            await drag_and_drop_component(page, "IBAN")
            # save with the defaults
            await close_modal(page, "Save", exact=True)

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
            await close_modal(page, "Save", exact=True)

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

    @skip_on_webtest
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
                await page.get_by_role("button", name="Advanced").click()
                await page.get_by_title("Advanced options").click()
                await page.locator("[name='triggerFromStep']").select_option(
                    label="Playwright test"
                )
                editor = page.locator(".monaco-editor")
                await enter_json_in_editor(page, editor, {"==": [1, 1]})

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
                await page.get_by_role("link", name="Validation").click()
                await page.get_by_role("button", name="Minimum date").click()

                # select the validation mode in the dropdown
                dropdown = page.get_by_role("combobox", name="Mode preset")
                await rs_select_option(dropdown, option_label="Relative to variable")

                # Fill in years, months, days and submit
                years = page.get_by_label("Years")
                months = page.get_by_label("Months")
                days = page.get_by_label("Days")
                await years.fill("1")
                await months.fill("1")
                await days.fill("1")
                await close_modal(page, "Save")

                # Navigate back to Validation
                await open_component_options_modal(page, "Some Field")
                await page.get_by_role("link", name="Validation").click()
                await page.get_by_role("button", name="Minimum date").click()

                # Check expectations
                await expect(years).to_have_value("1")
                await expect(months).to_have_value("1")
                await expect(months).to_have_value("1")

                await close_modal(page, "Save")

            with phase("Change values for datetime validation"):
                await open_component_options_modal(page, "Some Field")
                await page.get_by_role("link", name="Validation").click()
                await page.get_by_role("button", name="Minimum date").click()

                # Fill in years, months, days and submit
                years = page.get_by_label("Years")
                months = page.get_by_label("Months")
                days = page.get_by_label("Days")
                await years.fill("8")
                await months.fill("8")
                await days.fill("8")
                await close_modal(page, "Save")

                # Navigate back to Validation
                await open_component_options_modal(page, "Some Field")
                await page.get_by_role("link", name="Validation").click()
                await page.get_by_role("button", name="Minimum date").click()

                # Check expectations
                await expect(years).to_have_value("8")
                await expect(months).to_have_value("8")
                await expect(months).to_have_value("8")

                # close modal again
                await close_modal(page, "Cancel")

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
            await page.get_by_role("link", name="Validation").click()

            # Check the custom errors for the number component
            await page.get_by_role("button", name="Custom error messages").click()

            for index, attribute in enumerate(["required", "min", "max"]):
                with self.subTest(validator_key=attribute):
                    test_id = f"input-translatedErrors.nl[{index}].key"
                    locator = page.get_by_test_id(test_id)
                    await expect(locator).to_be_visible()
                    await expect(locator).to_have_value(attribute)

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
            sidebar = page.locator("css=.edit-panel__nav").get_by_role("list")
            bin_icon = sidebar.get_by_role("listitem").nth(0).get_by_title("Delete")
            await bin_icon.click()
            await page.get_by_role("button", name="Confirm").click()

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
            sidebar = page.locator("css=.edit-panel__nav").get_by_role("list")
            bin_icon = sidebar.get_by_role("listitem").nth(1).get_by_title("Delete")
            await bin_icon.click()
            await page.get_by_role("button", name="Confirm").click()

            await page.get_by_role("tab", name="Logic").click()

            # Check that you can delete the logic rule
            bin_icon = page.get_by_title("Delete").first
            await expect(bin_icon).to_be_visible()

            # Check that a warning is present
            warning = page.get_by_role("listitem").get_by_text(
                "The selected trigger step could not be found in this form! Please change it!"
            )
            await expect(warning).to_be_visible()

    @tag("gh-3921")
    async def test_all_components_are_visible_in_component_select_dropdown(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "field1",
                            "label": "Field 1",
                        },
                        {
                            "type": "fieldset",
                            "key": "fieldset",
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "field2",
                                    "label": "Field 2",
                                },
                            ],
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
            await open_component_options_modal(page, "Field 2")
            await page.get_by_role("tab", name="Location").click()

            dropdown = page.get_by_role("combobox", name="Postcode component")
            await dropdown.focus()
            await page.keyboard.press("ArrowDown")
            await expect(
                page.get_by_role("option", name="Field 1 (field1)")
            ).to_be_visible()

    @tag("gh-4061")
    async def test_column_components_are_visible_in_component_select_dropdown(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Playwright test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Playwright test",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "field1",
                            "label": "Field 1",
                        },
                        {
                            "type": "columns",
                            "key": "columns",
                            "columns": [
                                {
                                    "size": 6,
                                    "sizeMobile": 4,
                                    "width": 6,
                                    "offset": 0,
                                    "push": 0,
                                    "pull": 0,
                                    "currentWidth": 6,
                                    "components": [
                                        {
                                            "type": "textfield",
                                            "key": "field2",
                                            "label": "Field 2",
                                        },
                                    ],
                                }
                            ],
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
            await open_component_options_modal(page, "Field 1")
            await page.get_by_role("tab", name="Location").click()

            dropdown = page.get_by_role("combobox", name="Postcode component")
            await dropdown.focus()
            await page.keyboard.press("ArrowDown")
            await expect(
                page.get_by_role("option", name="Field 2 (field2)")
            ).to_be_visible()

    @tag("gh-4969")
    async def test_saving_form_does_not_reset_submission_counter(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(generate_minimal_setup=True, submission_counter=0)
            return form

        @sync_to_async
        def update_submission_counter(form: Form):
            form.submission_counter = 10
            form.save(update_fields=["submission_counter"])

        await create_superuser()
        form = await setUpTestData()
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await expect(
                page.get_by_role("tab", name="Steps and fields")
            ).to_be_visible()

            # now, after loading the form, modify the submission counter, simulating some
            # submissions happened while the form was opened in some admin screen.
            await update_submission_counter(form)

            # Save form
            await page.get_by_role("button", name="Save", exact=True).click()
            changelist_url = str(
                furl(self.live_server_url) / reverse("admin:forms_form_changelist")
            )
            await expect(page).to_have_url(changelist_url)

        @sync_to_async
        def assert_state(form: Form):
            form.refresh_from_db()

            self.assertEqual(form.submission_counter, 10)

        await assert_state(form)


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
                            "openForms": {"dataSrc": DataSrcOptions.manual},
                            "values": [
                                {"value": "option", "label": "Option"},
                            ],
                        },
                        {
                            "type": "select",
                            "key": "select",
                            "label": "Select 1",
                            "openForms": {"dataSrc": DataSrcOptions.manual},
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
                            "openForms": {"dataSrc": DataSrcOptions.manual},
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

                    await close_modal(page, "Cancel")


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
                            "initialCenter": {"lat": 52.132123, "lng": 6.5},
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
            await page.get_by_role("tab", name="Map settings").click()
            await page.get_by_role("button", name="Initial focus").click()
            # both fields are required so we clear one.
            await page.get_by_label("Latitude").clear()

            await click_modal_button(page, "Save")

            error_node = page.locator("css=.error")
            await expect(error_node).to_be_visible()
            await expect(error_node).to_have_text(
                "You need to configure both longitude and latitude."
            )

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
            await page.get_by_role("tab", name="Map settings").click()
            await page.get_by_role("button", name="Initial focus").click()
            # both fields are required so we clear one.
            await page.get_by_label("Longitude").clear()

            await click_modal_button(page, "Save")

            error_node = page.locator("css=.error")
            await expect(error_node).to_be_visible()
            await expect(error_node).to_have_text(
                "You need to configure both longitude and latitude."
            )


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
            await expect(page.get_by_label("Appointment enabled")).to_be_checked()

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
            await page.get_by_role("button", name="Sluiten").click()

            # Delete the second step
            sidebar = page.locator("css=.edit-panel__nav").get_by_role("list")
            await sidebar.get_by_role("listitem").nth(1).get_by_title("Delete").click()
            await page.get_by_role("button", name="Confirm").click()

            # Select third form step and open selectbox
            await (
                sidebar.get_by_role("listitem")
                .nth(1)
                .get_by_text("Stap 3 [new]")
                .click()
            )
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
