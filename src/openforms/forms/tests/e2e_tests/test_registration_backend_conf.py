from django.urls import resolve, reverse

from asgiref.sync import sync_to_async
from furl import furl

from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser

from ..factories import FormFactory
from .helpers import close_modal, open_component_options_modal, phase


class FormDesignerRegistrationBackendConfigTests(E2ETestCase):
    async def test_configuring_zgw_api_group(self):
        """
        Test that the admin editor dynamically changes the request to InformatieObjectTypenListView based on the registration backend configuration.

        The flow in this test is:
        - Configure the Registration backend to use set 1 of the configured ZGW apis
        - Go to the file upload component and check that the query parameter in the request to the informatieobjecttype endpoint is the PK of the right group
        - Go back to the registration tab and change which ZGW API group should be used
        - Go to the file component and check that the query parameter in the request changes
        """

        @sync_to_async
        def setUpTestData():
            zgw_api_1 = ZGWApiGroupConfigFactory.create(
                name="Group 1",
                zrc_service__api_root="https://zaken-1.nl/api/v1/",
                zrc_service__oas="https://zaken-1.nl/api/v1/schema/openapi.yaml",
                drc_service__api_root="https://documenten-1.nl/api/v1/",
                drc_service__oas="https://documenten-1.nl/api/v1/schema/openapi.yaml",
                ztc_service__api_root="https://catalogus-1.nl/api/v1/",
                ztc_service__oas="https://catalogus-1.nl/api/v1/schema/openapi.yaml",
            )
            zgw_api_2 = ZGWApiGroupConfigFactory.create(
                name="Group 2",
                zrc_service__api_root="https://zaken-2.nl/api/v1/",
                zrc_service__oas="https://zaken-2.nl/api/v1/schema/openapi.yaml",
                drc_service__api_root="https://documenten-2.nl/api/v1/",
                drc_service__oas="https://documenten-2.nl/api/v1/schema/openapi.yaml",
                ztc_service__api_root="https://catalogus-2.nl/api/v1/",
                ztc_service__oas="https://catalogus-2.nl/api/v1/schema/openapi.yaml",
            )
            form = FormFactory.create(
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
            return {
                "zgw_api_1": zgw_api_1,
                "zgw_api_2": zgw_api_2,
                "form": form,
            }

        await create_superuser()
        test_data = await setUpTestData()
        zgw_api_1 = test_data["zgw_api_1"]
        zgw_api_2 = test_data["zgw_api_2"]
        form = test_data["form"]

        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        requests_to_endpoint = []

        def collect_requests(request):
            url = furl(request.url)
            match = resolve(url.path)

            if match.view_name == "api:iotypen-list":
                requests_to_endpoint.append(request)

        async with browser_page() as page:
            page.on("request", collect_requests)

            await self._admin_login(page)
            await page.goto(str(admin_url))
            modal = page.locator("css=.formio-dialog-content")

            with phase("Configure registration backend"):
                await page.get_by_role("tab", name="Registration").click()
                await page.get_by_role(
                    "button", name="Add registration backend"
                ).click()
                await page.get_by_role(
                    "combobox", name="Select registration backend"
                ).select_option(label="ZGW API's")
                await page.get_by_label("ZGW API group").select_option(label="Group 1")

            with phase("Configure upload component"):
                await page.get_by_role("tab", name="Steps and fields").click()

                await open_component_options_modal(page, label="File upload test")
                await modal.get_by_role("tab", name="Registration").click()
                await close_modal(page, "Save")

            with phase("Update the ZGW API group configured"):
                await page.get_by_role("tab", name="Registration").click()
                await page.get_by_role(
                    "combobox", name="Select registration backend"
                ).select_option(label="ZGW API's")
                await page.get_by_label("ZGW API group").select_option(label="Group 2")

            with phase("Reopen the upload component"):
                await page.get_by_role("tab", name="Steps and fields").click()

                await open_component_options_modal(page, label="File upload test")
                await modal.get_by_role("tab", name="Registration").click()
                await close_modal(page, "Save")

        self.assertEqual(len(requests_to_endpoint), 2)
        self.assertEqual(
            furl(requests_to_endpoint[0].url).args["zgw_api_group"],
            str(zgw_api_1.pk),
        )
        self.assertEqual(
            furl(requests_to_endpoint[0].url).args["registration_backend"],
            "zgw-create-zaak",
        )
        self.assertEqual(
            furl(requests_to_endpoint[1].url).args["zgw_api_group"],
            str(zgw_api_2.pk),
        )
        self.assertEqual(
            furl(requests_to_endpoint[1].url).args["registration_backend"],
            "zgw-create-zaak",
        )

    async def test_configuration_objects_api_backend(self):
        @sync_to_async
        def setUpTestData():
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
            match = resolve(str(url.path))

            if match.view_name == "api:iotypen-list":
                requests_to_endpoint.append(request)

        async with browser_page() as page:
            page.on("request", collect_requests)

            await self._admin_login(page)
            await page.goto(str(admin_url))

            with phase("Configure registration backend"):
                await page.get_by_role("tab", name="Registration").click()
                await page.get_by_role(
                    "button", name="Add registration backend"
                ).click()
                await page.get_by_role(
                    "combobox", name="Select registration backend"
                ).select_option(label="Objects API registration")

            with phase("Configure upload component"):
                await page.get_by_role("tab", name="Steps and fields").click()

                await open_component_options_modal(page, label="File upload test")
                modal = page.locator("css=.formio-dialog-content")
                await modal.get_by_role("tab", name="Registration").click()
                await close_modal(page, "Save")

        self.assertEqual(len(requests_to_endpoint), 1)
        self.assertEqual(
            furl(requests_to_endpoint[0].url).args["registration_backend"],
            "objects_api",
        )
