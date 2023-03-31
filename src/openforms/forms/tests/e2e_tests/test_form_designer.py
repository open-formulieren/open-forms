import re
from contextlib import contextmanager

from django.test import tag
from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import Page, expect

from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..factories import (
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
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
    await page.locator('css=[ref="-container"]').hover()
    await page.mouse.up()


async def open_component_options_modal(page: Page, label: str):
    """
    Find the component in the builder with the given label and click the edit icon
    to bring up the options modal.
    """
    # hover over component to bring up action icons
    await page.get_by_text(label).hover()
    # formio doesn't have accessible roles here, so use CSS selector
    await page.locator('css=[ref="editComponent"]').locator("visible=true").click()
    # check that the modal is open now
    await expect(page.locator("css=.formio-dialog-content")).to_be_visible()


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
                await open_component_options_modal(page, "Field 1")

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
                await open_component_options_modal(page, "Field 2")
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
            await page.get_by_role("link", name="Vertalingen").click()
            literal = page.locator('css=[name="data[openForms.translations.nl][0]"]')
            translation = page.locator(
                'css=[name="data[openForms.translations.nl][0][translation]"]'
            )
            await expect(literal).to_have_value("Test")
            await expect(translation).to_have_value("")

            await translation.click()
            await translation.fill("Vertaald label")

            # Now change the source string & check the translations are still in place
            await page.get_by_role("link", name="Basis").click()
            await page.get_by_label("Label", exact=True).fill("Test 2")

            await page.get_by_role("link", name="Vertalingen").click()
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
            key_input = page.get_by_label("Eigenschapnaam")
            await expect(key_input).to_have_value("file")

            # Modify the component label
            label_input = page.get_by_label("Label")
            await label_input.click()
            await label_input.fill("Test")

            # Test that the key also changed
            await expect(key_input).to_have_value("test")

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
            key_input = page.get_by_label("Eigenschapnaam")
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
            await page.get_by_role("button", name="Opslaan").first.click()

            # the modal should close
            await expect(page.locator("css=.formio-dialog-content")).to_be_hidden()

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
            # import bpdb; bpdb.set_trace()
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
                await page.get_by_role("button", name="Annuleren").click()

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
