from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser

from ...models import FormLogic
from ..factories import FormFactory
from .helpers import enter_json_in_editor, skip_on_webtest


class LogicTabTests(E2ETestCase):
    @skip_on_webtest
    async def test_make_component_not_required_with_logic(self):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Form with logic",
                formstep__form_definition__slug="form-with-logic",
                formstep__form_definition__name="Some step",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "textfield",
                            "key": "field1",
                            "label": "Some Field",
                        },
                    ],
                },
                generate_minimal_setup=True,
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
            await page.get_by_role("tab", name="Logic").click()
            await page.get_by_text("Add rule").click()
            await page.get_by_role("button", name="Advanced").click()

            await enter_json_in_editor(page, page.locator(".monaco-editor"), True)

            await page.get_by_text("Add Action").click()
            await page.locator('select[name="action.type"]').select_option(
                label="change a property of a component."
            )
            await page.locator('select[name="component"]').last.select_option(
                label="Some step: Some Field (field1)"
            )
            await page.locator('select[name="action.property"]').select_option(
                label="required"
            )
            await page.locator('select[name="action.state"]').select_option(label="Yes")

            await page.get_by_text("Save and continue editing").click()

            change_form_header = page.get_by_role("heading", name="Change form")

            await expect(change_form_header).to_be_visible()

            @sync_to_async
            def assertState():
                rule = FormLogic.objects.get()

                self.assertEqual(
                    rule.actions[0],
                    {
                        "component": "field1",
                        "action": {
                            "type": "property",
                            "property": {"value": "validate.required", "type": "bool"},
                            "state": True,
                        },
                    },
                )

            await assertState()
