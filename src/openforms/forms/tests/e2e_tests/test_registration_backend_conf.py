from django.urls import resolve, reverse

from asgiref.sync import sync_to_async
from furl import furl

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.registrations.contrib.zgw_apis.tests.factories import (
    ZGWApiGroupConfigFactory,
)
from openforms.tests.e2e.base import (
    E2ETestCase,
    browser_page,
    create_superuser,
    rs_select_option,
)
from openforms.utils.tests.vcr import OFVCRMixin

from ..factories import FormFactory
from .helpers import close_modal, open_component_options_modal, phase


class FormDesignerRegistrationBackendConfigTests(OFVCRMixin, E2ETestCase):
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
                drc_service__api_root="https://documenten-1.nl/api/v1/",
                ztc_service__api_root="https://catalogus-1.nl/api/v1/",
            )
            zgw_api_2 = ZGWApiGroupConfigFactory.create(
                name="Group 2",
                zrc_service__api_root="https://zaken-2.nl/api/v1/",
                drc_service__api_root="https://documenten-2.nl/api/v1/",
                ztc_service__api_root="https://catalogus-2.nl/api/v1/",
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
            # ignore about:* URLs
            if url.scheme == "about":
                return

            match = resolve(str(url.path))
            if match.view_name == "api:zgw_apis:document-type-list":
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
                await page.get_by_role("button", name="Configure options").click()

                config_modal = page.get_by_role("dialog")
                await rs_select_option(
                    config_modal.get_by_role("combobox", name="API group"),
                    option_label="Group 1",
                )
                await config_modal.get_by_role("button", name="Save").click()

            with phase("Configure upload component"):
                await page.get_by_role("tab", name="Steps and fields").click()

                await open_component_options_modal(page, label="File upload test")
                await modal.get_by_role("tab", name="Registration").click()
                await close_modal(page, "Save")

            with phase("Update the ZGW API group configured"):
                await page.get_by_role("tab", name="Registration").click()
                await page.get_by_role("button", name="Configure options").click()

                config_modal = page.get_by_role("dialog")
                await rs_select_option(
                    config_modal.get_by_role("combobox", name="API group"),
                    option_label="Group 2",
                )
                await config_modal.get_by_role("button", name="Save").click()

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

    async def test_configuration_objects_api_group(self):
        """
        Assert that the document types are retrieved based on the selected API group.

        This test uses VCR, when re-recording cassettes, ensure that the docker-compose
        services are up and running. From the root of the repo:

        .. code-block:: bash

            cd docker
            docker compose \
                -f docker-compose.open-zaak.yml \
                -f docker-compose.objects-apis.yml \
                up
        """

        @sync_to_async
        def setUpTestData():
            # both groups talk to the same services for simplicity
            objects_api_1 = ObjectsAPIGroupConfigFactory.create(
                name="Group 1",
                for_test_docker_compose=True,
            )
            objects_api_2 = ObjectsAPIGroupConfigFactory.create(
                name="Group 2",
                for_test_docker_compose=True,
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
            # ignore about:* URLs
            if url.scheme == "about":
                return

            match = resolve(str(url.path))
            if match.view_name == "api:objects_api:document-type-list":
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
                await rs_select_option(
                    config_modal.get_by_role("combobox", name="API group"),
                    option_label="Group 1",
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
                await rs_select_option(
                    config_modal.get_by_role("combobox", name="API group"),
                    option_label="Group 2",
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
            str(objects_api_1.identifier),
        )
        self.assertEqual(
            furl(requests_to_endpoint[1].url).args["objects_api_group"],
            str(objects_api_2.identifier),
        )
