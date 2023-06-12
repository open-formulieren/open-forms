from django.urls import resolve, reverse

from asgiref.sync import sync_to_async
from furl import furl

from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser

from ..factories import FormFactory
from .test_form_designer import open_component_options_modal, phase


class FormDesignerRegistrationBackendConfigTests(E2ETestCase):
    async def test_configuring_zgw_api_group(self):
        """
        The flow in this test is:
        - Configure the Registration backend to use set 1 of the configured ZGW apis
        - Go to the file upload component and check that the query parameter in the request to the informatieobjecttype endpoint is the PK of the right group
        - Go back to the registration tab and change which ZGW API group should be used
        - Go to the file component and check that the query parameter in the request changes
        """

        @sync_to_async
        def setUpTestData():
            self.zgw_api_1 = ZGWApiGroupConfigFactory.create(
                name="Group 1",
                zrc_service__api_root="https://zaken-1.nl/api/v1/",
                zrc_service__oas="https://zaken-1.nl/api/v1/schema/openapi.yaml",
                drc_service__api_root="https://documenten-1.nl/api/v1/",
                drc_service__oas="https://documenten-1.nl/api/v1/schema/openapi.yaml",
                ztc_service__api_root="https://catalogus-1.nl/api/v1/",
                ztc_service__oas="https://catalogus-1.nl/api/v1/schema/openapi.yaml",
            )
            self.zgw_api_2 = ZGWApiGroupConfigFactory.create(
                name="Group 2",
                zrc_service__api_root="https://zaken-2.nl/api/v1/",
                zrc_service__oas="https://zaken-2.nl/api/v1/schema/openapi.yaml",
                drc_service__api_root="https://documenten-2.nl/api/v1/",
                drc_service__oas="https://documenten-2.nl/api/v1/schema/openapi.yaml",
                ztc_service__api_root="https://catalogus-2.nl/api/v1/",
                ztc_service__oas="https://catalogus-2.nl/api/v1/schema/openapi.yaml",
            )

            return FormFactory.create(
                name="Configure registration test",
                name_nl="Configure registration test",
                generate_minimal_setup=True,
                formstep__form_definition__name_nl="Configure registration test",
                formstep__form_definition__configuration={
                    "components": [
                        {
                            "type": "file",
                            "key": "fileUpload",
                            "label": "File upload test",
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

        requests_to_endpoint = []

        def collect_requests(request):
            url = furl(request.url)
            match = resolve(url.path)

            if match.view_name == "api:zgw_apis:iotypen-list":
                requests_to_endpoint.append(request)

        async with browser_page() as page:
            page.on("request", collect_requests)

            await self._admin_login(page)
            await page.goto(str(admin_url))

            with phase("Configure registration backend"):
                await page.get_by_role("tab", name="Registration").click()
                await page.get_by_role(
                    "combobox", name="Select registration backend"
                ).select_option(label="ZGW API's")
                await page.get_by_label("ZGW API set").select_option(label="Group 1")

            with phase("Configure upload component"):
                await page.get_by_role("tab", name="Steps and fields").click()

                await open_component_options_modal(page, label="File upload test")
                await page.get_by_role("button", name="Opslaan").first.click()

            with phase("Update the ZGW API group configured"):
                await page.get_by_role("tab", name="Registration").click()
                await page.get_by_role(
                    "combobox", name="Select registration backend"
                ).select_option(label="ZGW API's")
                await page.get_by_label("ZGW API set").select_option(label="Group 2")

            with phase("Reopen the upload component"):
                await page.get_by_role("tab", name="Steps and fields").click()

                await open_component_options_modal(page, label="File upload test")
                await page.get_by_role("button", name="Opslaan").first.click()

        # Formio fires the request twice everytime you open the component
        self.assertEqual(len(requests_to_endpoint), 4)
        self.assertEqual(
            furl(requests_to_endpoint[0]).args["zgw_api_group"], str(self.zgw_api_1.pk)
        )
        self.assertEqual(
            furl(requests_to_endpoint[2]).args["zgw_api_group"], str(self.zgw_api_2.pk)
        )
