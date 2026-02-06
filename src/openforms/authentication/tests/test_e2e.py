from unittest.mock import patch

from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import expect

from openforms.forms.tests.factories import FormFactory
from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser


class RegistratorSubjectInfoTests(E2ETestCase):
    async def test_registrator_subject_info_page(self):
        @sync_to_async
        def setUpTestData():
            return FormFactory.create(
                generate_minimal_setup=True, authentication_backend="org-oidc"
            )

        await create_superuser()
        form = await setUpTestData()

        form_url = str(
            furl(self.live_server_url)
            / reverse("forms:form-detail", kwargs={"slug": form.slug})
        )
        registrator_page = furl(self.live_server_url) / reverse(
            "authentication:registrator-subject", kwargs={"slug": form.slug}
        )
        registrator_page.args.set("next", form_url)

        async with browser_page() as page:
            await self._admin_login(page)

            with patch(
                "openforms.authentication.views.allow_redirect_url", return_value=True
            ):
                await page.goto(registrator_page.url)

            await page.get_by_label("Citizen").click()
            bsn_input = page.get_by_role("textbox", name="bsn")
            kvk_input = page.get_by_role("textbox", name="kvk")
            employee_button = page.get_by_role(
                "button", name="Continue without additional information"
            )

            await expect(bsn_input).to_be_visible()
            await expect(kvk_input).not_to_be_visible()
            await expect(employee_button).not_to_be_visible()

            await page.get_by_label("Company").click()

            bsn_input = page.get_by_role("textbox", name="bsn")
            kvk_input = page.get_by_label("KvK number of customer")
            employee_button = page.get_by_role(
                "button", name="Continue without additional information"
            )

            await expect(bsn_input).not_to_be_visible()
            await expect(kvk_input).to_be_visible()
            await expect(employee_button).not_to_be_visible()

            await page.get_by_label("Employee").click()

            bsn_input = page.get_by_role("textbox", name="bsn")
            kvk_input = page.get_by_role("textbox", name="kvk")
            employee_button = page.get_by_role(
                "button", name="Continue without additional information"
            )

            await expect(bsn_input).not_to_be_visible()
            await expect(kvk_input).not_to_be_visible()
            await expect(employee_button).to_be_visible()
