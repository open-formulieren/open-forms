from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect
from zgw_consumers.test.factories import ServiceFactory

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory


class ServiceFetchConfigTests(E2ETestCase):
    async def test_set_cache_timeout(
        self,
    ):
        @sync_to_async
        def setUpTestData():
            # set up a form
            form = FormFactory.create(
                name="Test service fetch configuration with cache timeout",
            )
            FormStepFactory.create(
                form=form,
            )
            service = ServiceFactory.create()
            fetch_config = ServiceFetchConfigurationFactory.create(
                service=service, path="get"
            )
            FormVariableFactory.create(
                form=form,
                name="Variable A",
                key="fieldA",
                user_defined=True,
                service_fetch_configuration=fetch_config,
            )

            FormLogicFactory.create(
                form=form,
                is_advanced=True,
                json_logic_trigger=True,
                actions=[
                    {
                        "variable": "fieldA",
                        "action": {
                            "name": "Fetch some field from some server",
                            "type": LogicActionTypes.fetch_from_service,
                            "value": fetch_config.id,
                        },
                    }
                ],
            )
            return form, service

        await create_superuser()
        form, service = await setUpTestData()
        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        async with browser_page() as page:
            await self._admin_login(page)
            await page.goto(str(admin_url))
            await page.get_by_role("tab", name="Logic").click()
            await page.get_by_role("button", name="Configure").click()

            await page.get_by_label("Cache timeout").press("ArrowUp")
            await page.get_by_role("button", name="Update").click()
            await page.get_by_role("button", name="Save and continue editing").click()

            await page.get_by_role("tab", name="Logic").click()
            await page.get_by_role("button", name="Configure").click()

            cache_timeout_field = page.get_by_label("Cache timeout")
            await expect(cache_timeout_field).to_have_value("1")
