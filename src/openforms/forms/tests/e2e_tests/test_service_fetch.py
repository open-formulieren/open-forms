from contextlib import contextmanager

from django.urls import reverse

from asgiref.sync import sync_to_async
from furl import furl
from playwright.async_api import Page, expect
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from openforms.config.models import GlobalConfiguration
from openforms.tests.e2e.base import E2ETestCase, browser_page, create_superuser
from openforms.variables.constants import DataMappingTypes, FormVariableSources
from openforms.variables.models import ServiceFetchConfiguration
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ..factories import FormFactory, FormVariableFactory


@contextmanager
def phase(desc: str):
    yield


async def add_new_variable_with_service_fetch(page: Page):
    await page.get_by_role("tab", name="Logic").click()

    await page.get_by_text("Add rule").click()
    await page.get_by_text("Simple").click()

    await page.locator('select[name="variable"]').select_option(
        label="Environment (environment)"
    )
    await page.locator('select[name="operator"]').select_option(label="is equal to")
    await page.locator('select[name="operandType"]').select_option(label="value")
    await page.locator('input[name="operand"]').fill("foo")

    await page.get_by_text("Add action").click()
    await page.locator('select[name="action.type"]').select_option(
        label="fetch the value for a variable from a service"
    )
    # FIXME Name conflict with the select above
    await page.locator('select[name="variable"]').last.select_option(
        label="Variable 1 (variable1)"
    )

    await expect(
        page.get_by_text("Fetch configuration: (not configured yet)")
    ).to_have_count(1)


async def fill_in_service_fetch_form(page: Page, data: dict, save_text: str = "Save"):
    await page.get_by_label("Name").fill(data["name"])
    await page.get_by_label("HTTP method").select_option(data["method"])
    await page.get_by_label("Service").select_option(label=data["service"])
    await page.get_by_label("Path").fill(data["path"])

    await page.locator('input[name="key"]').first.fill(
        list(data["query_params"].items())[0][0]
    )
    await page.locator('input[name="value-0"]').fill(
        list(data["query_params"].items())[0][1][0]
    )
    await page.locator('input[name="key"]').last.fill(
        list(data["headers"].items())[0][0]
    )
    await page.locator('input[name="value"]').fill(list(data["headers"].items())[0][1])

    # FIXME doesn't seem to work with `get_by_label`
    await page.locator('textarea[name="body"]').fill(data["request_body"])

    await page.get_by_label("Mapping expression language").select_option(
        data["data_mapping_type"]
    )
    if data["data_mapping_type"] == DataMappingTypes.json_logic:
        await page.locator('textarea[name="jsonLogicExpression"]').fill(
            data["mapping_expression"]
        )
    else:
        await page.get_by_label("Mapping expression", exact=True).fill(
            data["mapping_expression"]
        )

    await page.get_by_role("button", name=save_text).click()


async def check_service_fetch_form_values(page: Page, data: dict):
    await expect(page.get_by_label("Name")).to_have_value(data["name"])
    await expect(page.get_by_label("HTTP method")).to_have_value(data["method"])

    # TODO fix this
    # await expect(page.get_by_label(
    #     "Service"
    # )).to_have_text(data["service"])
    await expect(page.get_by_label("Path")).to_have_value(data["path"])

    await expect(page.locator('input[name="key"]').first).to_have_value(
        list(data["query_params"].items())[0][0]
    )
    await expect(page.locator('input[name="value-0"]')).to_have_value(
        list(data["query_params"].items())[0][1][0]
    )
    await expect(page.locator('input[name="key"]').last).to_have_value(
        list(data["headers"].items())[0][0]
    )
    await expect(page.locator('input[name="value"]')).to_have_value(
        list(data["headers"].items())[0][1]
    )

    # FIXME doesn't seem to work with `get_by_label`
    await expect(page.locator('textarea[name="body"]')).to_have_value(
        data["request_body"]
    )

    await expect(page.get_by_label("Mapping expression language")).to_have_value(
        data["data_mapping_type"]
    )
    if data["data_mapping_type"] == DataMappingTypes.json_logic:
        await expect(
            page.locator('textarea[name="jsonLogicExpression"]')
        ).to_have_value(data["mapping_expression"])
    else:
        await expect(page.get_by_label("Mapping expression", exact=True)).to_have_value(
            data["mapping_expression"]
        )


class FormDesignerServiceFetchConfigurationTests(E2ETestCase):
    def setUp(self):
        super().setUp()

        global_config = GlobalConfiguration.get_solo()
        global_config.enable_service_fetch = True
        global_config.save()

        self.service = Service.objects.create(
            label="Test",
            api_type=APITypes.orc,
            auth_type=AuthTypes.no_auth,
        )
        self.service_url = reverse("api:service-detail", kwargs={"pk": 1})

    async def test_service_fetch_configuration_create_new(self):
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
            FormVariableFactory.create(
                form=form, name="Variable 1", key="variable1", user_defined=True
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

            await add_new_variable_with_service_fetch(page)

            await page.get_by_role("button", name="Configure").click()

            data = {
                "name": "Service fetch config #1",
                "method": "POST",
                "service": "Test",
                "path": "bar",
                "query_params": {"param": ["paramvalue"]},
                "headers": {"header": "headervalue"},
                "request_body": '{\n  "foo": "bar"\n}',
                "data_mapping_type": DataMappingTypes.json_logic,
                "mapping_expression": '{\n  "==": [\n    1,\n    1\n  ]\n}',
            }

            await fill_in_service_fetch_form(page, data)

            # TODO check if name is shown
            # TODO reopen modal and check if proper info filled
            await expect(
                page.get_by_text("Fetch configuration: Service fetch config #1")
            ).to_be_visible()
            await page.get_by_role("button", name="Configure").click()
            await check_service_fetch_form_values(page, data)
            await page.get_by_title("Sluiten").click()

            await page.get_by_text("Save and continue editing").click()
            await page.get_by_role("tab", name="Logic").click()

            await expect(
                page.get_by_text("Fetch configuration: Service fetch config #1")
            ).to_be_visible()
            await page.get_by_role("button", name="Configure").click()
            await check_service_fetch_form_values(page, data)

            @sync_to_async
            def assertState():
                self.assertEqual(ServiceFetchConfiguration.objects.count(), 1)

                user_defined_vars = form.formvariable_set.filter(
                    source=FormVariableSources.user_defined
                )

                self.assertEqual(user_defined_vars.count(), 1)

                created_var = user_defined_vars.first()

                self.assertEqual(
                    created_var.service_fetch_configuration.name,
                    "Service fetch config #1",
                )

            await assertState()

    async def test_service_fetch_configuration_create_new_jq(self):
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
            FormVariableFactory.create(
                form=form, name="Variable 1", key="variable1", user_defined=True
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

            await add_new_variable_with_service_fetch(page)

            await page.get_by_role("button", name="Configure").click()

            data = {
                "name": "Service fetch config #1",
                "method": "POST",
                "service": "Test",
                "path": "bar",
                "query_params": {"param": ["paramvalue"]},
                "headers": {"header": "headervalue"},
                "request_body": '{\n  "foo": "bar"\n}',
                "data_mapping_type": DataMappingTypes.jq,
                "mapping_expression": ".foo",
            }

            await fill_in_service_fetch_form(page, data)

            # TODO check if name is shown
            # TODO reopen modal and check if proper info filled
            await expect(
                page.get_by_text("Fetch configuration: Service fetch config #1")
            ).to_be_visible()
            await page.get_by_role("button", name="Configure").click()
            await check_service_fetch_form_values(page, data)
            await page.get_by_title("Sluiten").click()

            await page.get_by_text("Save and continue editing").click()
            await page.get_by_role("tab", name="Logic").click()

            await expect(
                page.get_by_text("Fetch configuration: Service fetch config #1")
            ).to_be_visible()
            await page.get_by_role("button", name="Configure").click()
            await check_service_fetch_form_values(page, data)

            @sync_to_async
            def assertState():
                self.assertEqual(ServiceFetchConfiguration.objects.count(), 1)

                user_defined_vars = form.formvariable_set.filter(
                    source=FormVariableSources.user_defined
                )

                self.assertEqual(user_defined_vars.count(), 1)

                created_var = user_defined_vars.first()

                self.assertEqual(
                    created_var.service_fetch_configuration.name,
                    "Service fetch config #1",
                )

            await assertState()

    async def test_service_fetch_configuration_save_existing_as_new(self):
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
            FormVariableFactory.create(
                form=form, name="Variable 1", key="variable1", user_defined=True
            )
            ServiceFetchConfigurationFactory.create(
                name="foo",
                method="POST",
                service=Service.objects.create(
                    label="Test service 2",
                    api_type=APITypes.orc,
                    auth_type=AuthTypes.no_auth,
                    api_root="/foo",
                ),
                path="foo",
                query_params={"foo": ["bar", "baz"]},
                headers={"header1": "value1"},
                body={"foo": "bar"},
                data_mapping_type=DataMappingTypes.jq,
                mapping_expression=".foo",
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

            await add_new_variable_with_service_fetch(page)

            await page.get_by_role("button", name="Configure").click()
            await page.get_by_label("Choose existing configuration").select_option(
                "foo"
            )

            await check_service_fetch_form_values(
                page,
                dict(
                    name="foo",
                    method="POST",
                    service="Test service 2",
                    path="foo",
                    query_params={"foo": ["bar"]},
                    headers={"header1": "value1"},
                    request_body='{\n  "foo": "bar"\n}',
                    data_mapping_type=DataMappingTypes.jq,
                    mapping_expression=".foo",
                ),
            )

            await fill_in_service_fetch_form(
                page,
                dict(
                    name="foo2",
                    method="POST",
                    service="Test service 2",
                    path="foo",
                    query_params={"foo": ["bar"]},
                    headers={"header1": "value1"},
                    request_body='{\n  "foo": "bar"\n}',
                    data_mapping_type=DataMappingTypes.jq,
                    mapping_expression=".bar",
                ),
                save_text="Save as new",
            )

            # TODO check if name is shown
            # TODO reopen modal and check if proper info filled
            await expect(page.get_by_text("Fetch configuration: foo2")).to_be_visible()
            await page.get_by_role("button", name="Configure").click()
            await check_service_fetch_form_values(
                page,
                dict(
                    name="foo2",
                    method="POST",
                    service="Test service 2",
                    path="foo",
                    query_params={"foo": ["bar"]},
                    headers={"header1": "value1"},
                    request_body='{\n  "foo": "bar"\n}',
                    data_mapping_type=DataMappingTypes.jq,
                    mapping_expression=".bar",
                ),
            )
            await page.get_by_title("Sluiten").click()

            await page.get_by_text("Save and continue editing").click()
            await page.get_by_role("tab", name="Logic").click()

            await expect(page.get_by_text("Fetch configuration: foo2")).to_be_visible()
            await page.get_by_role("button", name="Configure").click()
            await check_service_fetch_form_values(
                page,
                dict(
                    name="foo2",
                    method="POST",
                    service="Test service 2",
                    path="foo",
                    query_params={"foo": ["bar"]},
                    headers={"header1": "value1"},
                    request_body='{\n  "foo": "bar"\n}',
                    data_mapping_type=DataMappingTypes.jq,
                    mapping_expression=".bar",
                ),
            )

            @sync_to_async
            def assertState():
                self.assertEqual(ServiceFetchConfiguration.objects.count(), 2)

                user_defined_vars = form.formvariable_set.filter(
                    source=FormVariableSources.user_defined
                )

                self.assertEqual(user_defined_vars.count(), 1)

                created_var = user_defined_vars.first()

                self.assertEqual(created_var.service_fetch_configuration.name, "foo2")

            await assertState()

    async def test_service_fetch_configuration_update_existing(self):
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
            FormVariableFactory.create(
                form=form, name="Variable 1", key="variable1", user_defined=True
            )
            ServiceFetchConfigurationFactory.create(
                name="foo",
                method="POST",
                service=Service.objects.create(
                    label="Test service 2",
                    api_type=APITypes.orc,
                    auth_type=AuthTypes.no_auth,
                    api_root="/foo",
                ),
                path="foo",
                query_params={"foo": ["bar", "baz"]},
                headers={"header1": "value1"},
                body={"foo": "bar"},
                data_mapping_type=DataMappingTypes.jq,
                mapping_expression=".foo",
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

            await add_new_variable_with_service_fetch(page)

            await page.get_by_role("button", name="Configure").click()
            await page.get_by_label("Choose existing configuration").select_option(
                "foo"
            )

            await check_service_fetch_form_values(
                page,
                dict(
                    name="foo",
                    method="POST",
                    service="Test service 2",
                    path="foo",
                    query_params={"foo": ["bar"]},
                    headers={"header1": "value1"},
                    request_body='{\n  "foo": "bar"\n}',
                    data_mapping_type=DataMappingTypes.jq,
                    mapping_expression=".foo",
                ),
            )

            await fill_in_service_fetch_form(
                page,
                dict(
                    name="foo2",
                    method="POST",
                    service="Test service 2",
                    path="foo",
                    query_params={"foo": ["bar"]},
                    headers={"header1": "value1"},
                    request_body='{\n  "foo": "bar"\n}',
                    data_mapping_type=DataMappingTypes.jq,
                    mapping_expression=".bar",
                ),
                save_text="Update",
            )

            # TODO check if name is shown
            # TODO reopen modal and check if proper info filled
            await expect(page.get_by_text("Fetch configuration: foo2")).to_be_visible()
            await page.get_by_role("button", name="Configure").click()
            await check_service_fetch_form_values(
                page,
                dict(
                    name="foo2",
                    method="POST",
                    service="Test service 2",
                    path="foo",
                    query_params={"foo": ["bar"]},
                    headers={"header1": "value1"},
                    request_body='{\n  "foo": "bar"\n}',
                    data_mapping_type=DataMappingTypes.jq,
                    mapping_expression=".bar",
                ),
            )
            await page.get_by_title("Sluiten").click()

            await page.get_by_text("Save and continue editing").click()
            await page.get_by_role("tab", name="Logic").click()

            await expect(page.get_by_text("Fetch configuration: foo2")).to_be_visible()
            await page.get_by_role("button", name="Configure").click()
            await check_service_fetch_form_values(
                page,
                dict(
                    name="foo2",
                    method="POST",
                    service="Test service 2",
                    path="foo",
                    query_params={"foo": ["bar"]},
                    headers={"header1": "value1"},
                    request_body='{\n  "foo": "bar"\n}',
                    data_mapping_type=DataMappingTypes.jq,
                    mapping_expression=".bar",
                ),
            )

            @sync_to_async
            def assertState():
                self.assertEqual(ServiceFetchConfiguration.objects.count(), 1)

                user_defined_vars = form.formvariable_set.filter(
                    source=FormVariableSources.user_defined
                )

                self.assertEqual(user_defined_vars.count(), 1)

                created_var = user_defined_vars.first()

                self.assertEqual(created_var.service_fetch_configuration.name, "foo2")

            await assertState()
