from unittest.mock import MagicMock, patch

from django.urls import Resolver404, resolve, reverse

from asgiref.sync import sync_to_async
from furl import furl

from openforms.registrations.contrib.objects_api.tests.factories import (
    ObjectsAPIGroupConfigFactory,
)
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser
from openforms.tests.utils import log_flaky

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
            try:
                match = resolve(str(url.path))
            except Resolver404:
                print(f"Failed to resolve URL: {request.url}")
                log_flaky()
                return

            if match.view_name == "api:zgw_apis:iotypen-list":
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
            furl(requests_to_endpoint[1].url).args["zgw_api_group"],
            str(zgw_api_2.pk),
        )

    @patch(
        "openforms.registrations.contrib.objects_api.client.ObjecttypesClient.list_objecttype_versions"
    )
    @patch(
        "openforms.registrations.contrib.objects_api.client.ObjecttypesClient.list_objecttypes"
    )
    async def test_configuration_objects_api_group(
        self,
        m_list_objecttypes: MagicMock,
        m_list_objecttype_versions: MagicMock,
    ):
        """
        Test that the admin editor dynamically changes the request to
        InformatieObjectTypenListView based on the registration backend configuration.

        The flow in this test is:
        - Configure the Registration backend to use set 1 of the configured Object apis
        - Go to the file upload component and check that the query parameter in the
          request to the informatieobjecttype endpoint is the PK of the right group
        - Go back to the registration tab and change which Objects API group should be used
        - Go to the file component and check that the query parameter in the request changes
        """
        ot_root = "https://objecttypes-1.nl/api/v2/"
        # subset of fields, API spec is at
        # https://github.com/maykinmedia/objecttypes-api/
        m_list_objecttypes.return_value = [
            {
                "url": f"{ot_root}objecttypes/0879828e-823b-493e-9879-e310b1bfda77",
                "uuid": "0879828e-823b-493e-9879-e310b1bfda77",
                "name": "Some object type",
                "namePlural": "Some object types",
                "dataClassification": "open",
            }
        ]
        m_list_objecttype_versions.return_value = [{"version": 1, "status": "draft"}]

        @sync_to_async
        def setUpTestData():
            objects_api_1 = ObjectsAPIGroupConfigFactory.create(
                name="Group 1",
                objects_service__api_root="https://objects-1.nl/api/v1/",
                objecttypes_service__api_root=ot_root,
                drc_service__api_root="https://documenten-1.nl/api/v1/",
                catalogi_service__api_root="https://catalogus-1.nl/api/v1/",
            )
            objects_api_2 = ObjectsAPIGroupConfigFactory.create(
                name="Group 2",
                objects_service__api_root="https://objects-2.nl/api/v1/",
                objecttypes_service__api_root="https://objecttypes-2.nl/api/v1/",
                drc_service__api_root="https://documenten-2.nl/api/v1/",
                catalogi_service__api_root="https://catalogus-2.nl/api/v1/",
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
                "objects_api_1": objects_api_1,
                "objects_api_2": objects_api_2,
                "form": form,
            }

        await create_superuser()
        test_data = await setUpTestData()
        objects_api_1 = test_data["objects_api_1"]
        objects_api_2 = test_data["objects_api_2"]
        form = test_data["form"]

        admin_url = str(
            furl(self.live_server_url)
            / reverse("admin:forms_form_change", args=(form.pk,))
        )

        requests_to_endpoint = []

        def collect_requests(request):
            url = furl(request.url)
            try:
                match = resolve(str(url.path))
            except Resolver404:
                print(f"Failed to resolve URL: {request.url}")
                log_flaky()
                return

            if match.view_name == "api:objects_api:iotypen-list":
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
                ).select_option(label="Objects API registration")
                await page.get_by_role("button", name="Configure options").click()

                config_modal = page.get_by_role("dialog")
                await config_modal.get_by_label("API group").select_option(
                    label="Group 1"
                )
                await config_modal.get_by_role("button", name="Save").click()

            with phase("Configure upload component"):
                await page.get_by_role("tab", name="Steps and fields").click()

                await open_component_options_modal(page, label="File upload test")
                await modal.get_by_role("tab", name="Registration").click()
                await close_modal(page, "Save")

            with phase("Update the Objects API group configured"):
                await page.get_by_role("tab", name="Registration").click()
                await page.get_by_role(
                    "combobox", name="Select registration backend"
                ).select_option(label="Objects API registration")
                await page.get_by_role("button", name="Configure options").click()

                config_modal = page.get_by_role("dialog")
                await config_modal.get_by_label("API group").select_option(
                    label="Group 2"
                )
                await config_modal.get_by_role("button", name="Save").click()

            with phase("Reopen the upload component"):
                await page.get_by_role("tab", name="Steps and fields").click()

                await open_component_options_modal(page, label="File upload test")
                await modal.get_by_role("tab", name="Registration").click()
                await close_modal(page, "Save")

        self.assertEqual(len(requests_to_endpoint), 2)
        self.assertEqual(
            furl(requests_to_endpoint[0].url).args["objects_api_group"],
            str(objects_api_1.pk),
        )
        self.assertEqual(
            furl(requests_to_endpoint[1].url).args["objects_api_group"],
            str(objects_api_2.pk),
        )
