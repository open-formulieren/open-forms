import re
from contextlib import contextmanager

from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..factories import FormDefinitionFactory, FormFactory, FormStepFactory


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
            await page.get_by_text("Bestandsupload").hover()
            await page.mouse.down()
            await page.locator('css=[ref="-container"]').hover()
            await page.mouse.up()

            # Check that the modal is open
            await expect(page.locator("css=.formio-dialog-content")).to_have_count(1)

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

            # Drag and drop a component
            await page.get_by_text("Tekstveld").hover()
            await page.mouse.down()
            await page.locator('css=[ref="-container"]').hover()
            await page.mouse.up()

            # Check that the modal is open
            await expect(page.locator("css=.formio-dialog-content")).to_have_count(1)

            # Check that the key has been made unique (textField1 vs textField)
            key_input = page.get_by_label("Eigenschapnaam")
            await expect(key_input).to_have_value("textField1")


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
