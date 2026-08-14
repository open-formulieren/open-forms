import re

from django.test import tag
from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import Page, expect

from openforms.appointments.models import AppointmentsConfig
from openforms.products.tests.factories import ProductFactory
from openforms.tests.e2e.base import (
    E2ETestCase,
    browser_page,
    create_superuser,
)
from openforms.utils.tests.cache import clear_caches
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ...constants import FormTypeChoices
from ...models import Form
from ..factories import (
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
)
from .helpers import close_modal, open_component_options_modal, phase


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


class AppointmentFormTests(E2ETestCase):
    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

    async def test_appointment_form_nukes_irrelevant_configuration(self):
        @sync_to_async
        def setUpTestData():
            # set up an appointment plugin
            appointments_config = AppointmentsConfig.get_solo()
            appointments_config.plugin = "demo"
            appointments_config.save()

            self.addCleanup(AppointmentsConfig.clear_cache)

            # set up a form
            form = FormFactory.create(
                name="Playwright appointment test",
                generate_minimal_setup=True,
                type=FormTypeChoices.regular,
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

            await page.get_by_label("Appointment").click()
            await expect(page.get_by_label("Appointment")).to_be_checked()

            with phase("save form changes to backend"):
                await page.get_by_role("button", name="Save", exact=True).click()
                changelist_url = str(
                    furl(self.live_server_url) / reverse("admin:forms_form_changelist")
                )
                await expect(page).to_have_url(changelist_url)

        @sync_to_async
        def assertState():
            form.refresh_from_db()

            self.assertEqual(form.type, FormTypeChoices.appointment)
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
            await page.get_by_role("button", name="Close").click()

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
