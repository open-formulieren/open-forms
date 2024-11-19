from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import override_settings

from factory.django import FileField
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)
from openforms.forms.models import FormVariable
from openforms.forms.tests.factories import (
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import (
    DataMappingTypes,
    FormVariableDataTypes,
    FormVariableSources,
    ServiceFetchMethods,
)
from openforms.variables.models import ServiceFetchConfiguration
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory


@override_settings(LANGUAGE_CODE="en")
class FormVariableViewsetTest(APITestCase):
    def test_auth_required(self):
        form = FormFactory.create()
        url = reverse(
            "api:form-variables",
            kwargs={"uuid_or_slug": form.uuid},
        )

        response = self.client.put(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_staff_required(self):
        # add the permissions to verify we specifically check is_staff
        user = UserFactory.create(
            is_staff=False, user_permissions=["change_form", "view_form"]
        )
        form = FormFactory.create()
        url = reverse(
            "api:form-variables",
            kwargs={"uuid_or_slug": form.uuid},
        )

        self.client.force_authenticate(user=user)
        response = self.client.put(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_bulk_create_and_update(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form)
        form_definition = form_step.form_definition

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        form_variable1 = FormVariableFactory.create(
            form=form, form_definition=form_definition, key="variable1"
        )
        FormVariableFactory.create(
            form=form, form_definition=form_definition, key="variable2"
        )  # This variable will be deleted
        another_form_variable = (
            FormVariableFactory.create()
        )  # Not related to the same form!

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": form_variable1.key,
                "name": "Test",
                "source": form_variable1.source,
                "service_fetch_configuration": None,
                "data_type": form_variable1.data_type,
                "initial_value": form_variable1.initial_value,
            },  # Data of form_variable1
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "name": "variable3",
                "key": "variable3",
                "source": FormVariableSources.user_defined,
                "data_type": FormVariableDataTypes.string,
                "initial_value": None,
            },  # New variable
        ]

        self.client.force_authenticate(user)
        response = self.client.put(
            reverse(
                "api:form-variables",
                kwargs={"uuid_or_slug": form.uuid},
            ),
            data=data,
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        variables = FormVariable.objects.all()

        self.assertEqual(3, variables.count())
        self.assertTrue(variables.filter(key=another_form_variable.key).exists())

        form_variables = variables.filter(form=form)

        self.assertEqual(2, form_variables.count())
        self.assertTrue(form_variables.filter(key="variable1").exists())
        self.assertFalse(form_variables.filter(key="variable2").exists())
        self.assertTrue(form_variables.filter(key="variable3").exists())

    def test_it_accepts_inline_service_fetch_configs(self):
        designer = StaffUserFactory.create(user_permissions=["change_form"])
        service = ServiceFactory.create(
            api_type=APITypes.orc,
            api_root="http://testserver/api/v2",
            auth_type=AuthTypes.no_auth,
            oas_file=FileField(
                from_path=Path(settings.BASE_DIR) / "src" / "openapi.yaml"
            ),
        )
        form = FormFactory.create(generate_minimal_setup=True)
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver{form_path}"
        form_definition = form.formstep_set.get().form_definition
        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver{form_definition_path}"
        form_variables_path = reverse(
            "api:form-variables", kwargs={"uuid_or_slug": form.uuid}
        )

        self.client.force_authenticate(designer)
        response = self.client.put(
            form_variables_path,
            data=[
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "name": "x",
                    "key": "x",
                    "source": FormVariableSources.user_defined,
                    "data_type": FormVariableDataTypes.object,
                    "initial_value": None,
                    "service_fetch_configuration": {
                        "name": "GET foo",
                        "service": f"http://testserver{reverse('api:service-detail', kwargs={'pk': service.pk})}",
                        "path": form_variables_path,
                        "method": ServiceFetchMethods.post,
                        "headers": {"X-Header": "someValue"},
                        "queryParams": {"X-It": ["someThings", "some_things"]},
                        "body": {"X-Something": "someValue"},
                        "dataMappingType": DataMappingTypes.jq,
                        "mappingExpression": '{"X-It": "someThing"}',
                    },
                }
            ],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fetch_config = FormVariable.objects.get(key="x").service_fetch_configuration

        self.assertEqual(fetch_config.service_id, service.id)
        self.assertEqual(fetch_config.path, form_variables_path)
        self.assertEqual(fetch_config.method, ServiceFetchMethods.post)
        self.assertEqual(fetch_config.data_mapping_type, DataMappingTypes.jq)
        self.assertEqual(fetch_config.mapping_expression, '{"X-It": "someThing"}')
        self.assertEqual(fetch_config.body, {"X-Something": "someValue"})
        self.assertEqual(
            fetch_config.query_params, {"X-It": ["someThings", "some_things"]}
        )
        self.assertEqual(fetch_config.headers, {"X-Header": "someValue"})

    def test_it_updates_inline_service_fetch_configs(self):
        designer = StaffUserFactory.create(user_permissions=["change_form"])
        service = ServiceFactory.create(
            api_type=APITypes.orc,
            api_root="http://testserver/api/v2",
            auth_type=AuthTypes.no_auth,
            oas_file=FileField(
                from_path=Path(settings.BASE_DIR) / "src" / "openapi.yaml"
            ),
        )
        form = FormFactory.create(generate_minimal_setup=True)
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver{form_path}"
        form_definition = form.formstep_set.get().form_definition
        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver{form_definition_path}"
        form_variables_path = reverse(
            "api:form-variables", kwargs={"uuid_or_slug": form.uuid}
        )

        service_fetch_config = ServiceFetchConfigurationFactory.create_batch(
            4,
            service=service,
        )[1]

        self.client.force_authenticate(designer)
        response = self.client.put(
            form_variables_path,
            data=[
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "name": "x",
                    "key": "x",
                    "source": FormVariableSources.user_defined,
                    "data_type": FormVariableDataTypes.object,
                    "initial_value": None,
                    "service_fetch_configuration": {
                        "id": service_fetch_config.id,
                        "name": "GET foo",
                        "service": f"http://testserver{reverse('api:service-detail', kwargs={'pk': service.pk})}",
                        "path": form_variables_path,
                        "method": ServiceFetchMethods.get,
                        "data_mapping_type": DataMappingTypes.json_logic,
                        "mapping_expression": {
                            "var": [
                                0,
                                {
                                    "map": [
                                        {"if": {"==": [{"var": "key"}, "x"]}},
                                        {"var": ""},
                                    ]
                                },
                            ]
                        },
                    },
                }
            ],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # it shouldn't add or delete configs
        self.assertEqual(ServiceFetchConfiguration.objects.count(), 4)

        fetch_config = FormVariable.objects.get(key="x").service_fetch_configuration

        self.assertEqual(fetch_config.service_id, service.id)
        self.assertEqual(fetch_config.path, form_variables_path)
        self.assertEqual(fetch_config.method, ServiceFetchMethods.get)

    def test_inline_service_fetch_configs_can_return_errors(self):
        designer = StaffUserFactory.create(user_permissions=["change_form"])
        service = ServiceFactory.create(
            api_type=APITypes.orc,
            api_root="http://testserver/api/v2",
            auth_type=AuthTypes.no_auth,
            oas_file=FileField(
                from_path=Path(settings.BASE_DIR) / "src" / "openapi.yaml"
            ),
        )
        form = FormFactory.create(generate_minimal_setup=True)
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver{form_path}"
        form_definition = form.formstep_set.get().form_definition
        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver{form_definition_path}"
        form_variables_path = reverse(
            "api:form-variables", kwargs={"uuid_or_slug": form.uuid}
        )

        self.client.force_authenticate(designer)
        response = self.client.put(
            form_variables_path,
            data=[
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "name": "faulty_x",
                    "key": "x",
                    "source": FormVariableSources.user_defined,
                    "data_type": FormVariableDataTypes.string,
                    "initial_value": None,
                    "service_fetch_configuration": {
                        "name": "GET foo",
                        "service": f"http://testserver{reverse('api:service-detail', kwargs={'pk': service.pk})}",
                        "path": form_variables_path,
                        "method": ServiceFetchMethods.get,
                        "data_mapping_type": DataMappingTypes.json_logic,
                        "mapping_expression": {"bork": []},
                    },
                },
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "name": "faulty_y",
                    "key": "y",
                    "source": FormVariableSources.user_defined,
                    "data_type": FormVariableDataTypes.string,
                    "initial_value": None,
                    "service_fetch_configuration": {
                        "name": "GET foo",
                        "service": f"http://testserver{reverse('api:service-detail', kwargs={'pk': service.pk})}",
                        "path": form_variables_path,
                        "method": ServiceFetchMethods.get,
                        "data_mapping_type": DataMappingTypes.json_logic,
                        "mapping_expression": {"borkbork": []},
                    },
                },
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "name": "faulty_z",
                    "key": "z",
                    "source": FormVariableSources.user_defined,
                    "data_type": FormVariableDataTypes.string,
                    "initial_value": None,
                    "service_fetch_configuration": {
                        "id": -1,  # does not exist
                        "name": "GET foo",
                        "service": f"http://testserver{reverse('api:service-detail', kwargs={'pk': service.pk})}",
                        "path": form_variables_path,
                        "method": ServiceFetchMethods.get,
                        "data_mapping_type": DataMappingTypes.json_logic,
                        "mapping_expression": {"var": "x"},
                    },
                },
            ],
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()
        self.assertEqual(error["code"], "invalid")
        self.assertEqual(len(error["invalidParams"]), 3)
        self.assertEqual(
            error["invalidParams"][0]["name"],
            "0.serviceFetchConfiguration.mappingExpression",
        )
        self.assertEqual(
            error["invalidParams"][0]["code"],
            "json_logic_invalid",
        )
        self.assertEqual(
            error["invalidParams"][0]["reason"],
            "The expression could not be compiled (Unrecognized operation bork).",
        )

        self.assertEqual(
            error["invalidParams"][1]["name"],
            "1.serviceFetchConfiguration.mappingExpression",
        )
        self.assertEqual(
            error["invalidParams"][1]["code"],
            "json_logic_invalid",
        )
        self.assertEqual(
            error["invalidParams"][1]["reason"],
            "The expression could not be compiled (Unrecognized operation borkbork).",
        )

        self.assertEqual(
            error["invalidParams"][2]["reason"],
            "The service fetch configuration with identifier -1 does not exist",
        )
        self.assertEqual(
            error["invalidParams"][2]["name"],
            "2.serviceFetchConfiguration",
        )
        self.assertEqual(
            error["invalidParams"][2]["code"],
            "not_found",
        )

    def test_unique_together_key_form(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form)
        form_definition = form_step.form_definition

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "test-not-unique",
                "name": "Test 1",
                "source": FormVariableSources.user_defined,
                "data_type": FormVariableDataTypes.string,
                "initial_value": "",
            },
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "name": "Test 2",
                "key": "test-not-unique",
                "source": FormVariableSources.user_defined,
                "data_type": FormVariableDataTypes.string,
                "initial_value": "",
            },
        ]

        self.client.force_authenticate(user)
        response = self.client.put(
            reverse(
                "api:form-variables",
                kwargs={"uuid_or_slug": form.uuid},
            ),
            data=data,
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        error = response.json()

        self.assertEqual(error["code"], "invalid")
        self.assertEqual(1, len(error["invalidParams"]))
        self.assertEqual(
            error["invalidParams"][0]["reason"],
            "The variable key must be unique within a form",
        )
        self.assertEqual(
            error["invalidParams"][0]["code"],
            "unique",
        )
        self.assertEqual(
            error["invalidParams"][0]["name"],
            "1.key",
        )

    def test_list_form_variables(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()

        FormVariableFactory.create(form=form, key="vars.1")
        FormVariableFactory.create(form=form, key="vars.2")
        FormVariableFactory.create()  # Not related to the same form!

        self.client.force_authenticate(user)
        response = self.client.get(
            reverse(
                "api:form-variables",
                kwargs={"uuid_or_slug": form.uuid},
            ),
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_data = response.json()

        self.assertEqual(2, len(response_data))

        variables_keys = {variable["key"] for variable in response_data}
        self.assertEqual(variables_keys, {"vars.1", "vars.2"})

    def test_list_form_variables_source_filter(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user)

        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "test",
                    }
                ]
            },
        )
        form_variable1 = FormVariableFactory.create(
            form=form, source=FormVariableSources.user_defined, key="test1"
        )
        form_variable2 = FormVariableFactory.create(
            form=form, source=FormVariableSources.user_defined, key="test2"
        )

        response_user_defined = self.client.get(
            reverse("api:form-variables", kwargs={"uuid_or_slug": form.uuid}),
            {"source": FormVariableSources.user_defined},
        )

        self.assertEqual(status.HTTP_200_OK, response_user_defined.status_code)

        response_data = response_user_defined.json()

        self.assertEqual(2, len(response_data))

        variables_keys = [variable["key"] for variable in response_data]

        self.assertIn(form_variable1.key, variables_keys)
        self.assertIn(form_variable2.key, variables_keys)

        response_component = self.client.get(
            reverse("api:form-variables", kwargs={"uuid_or_slug": form.uuid}),
            {"source": FormVariableSources.component},
        )

        self.assertEqual(status.HTTP_200_OK, response_component.status_code)

        response_data = response_component.json()

        self.assertEqual(1, len(response_data))
        self.assertEqual("test", response_data[0]["key"])

    def test_list_form_variables_invalid_source(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user)

        form = FormFactory.create()
        FormVariableFactory.create(form=form, source=FormVariableSources.user_defined)

        response_user_defined = self.client.get(
            reverse("api:form-variables", kwargs={"uuid_or_slug": form.uuid}),
            {"invalid": FormVariableSources.user_defined},
        )

        self.assertEqual(status.HTTP_200_OK, response_user_defined.status_code)

        response_data = response_user_defined.json()

        self.assertEqual(1, len(response_data))

    def test_dotted_variable_keys(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form)
        form_definition = form_step.form_definition

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        data_valid = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "test-with_dots.valid",
                "name": "Valid with dots",
                "source": FormVariableSources.user_defined,
                "data_type": FormVariableDataTypes.string,
                "initial_value": "",
            },
        ]

        data_invalid = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "test-with_dots.invalid.",
                "name": "Valid with dots",
                "source": FormVariableSources.user_defined,
                "data_type": FormVariableDataTypes.string,
                "initial_value": "",
            },
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "normal_key",
                "name": "",  # missing name
                "source": FormVariableSources.user_defined,
                "data_type": FormVariableDataTypes.string,
                "initial_value": "",
            },
        ]

        self.client.force_authenticate(user)

        with self.subTest("Valid key"):
            response = self.client.put(
                reverse(
                    "api:form-variables",
                    kwargs={"uuid_or_slug": form.uuid},
                ),
                data=data_valid,
            )

            self.assertEqual(status.HTTP_200_OK, response.status_code)

        with self.subTest("Invalid key"):
            response = self.client.put(
                reverse(
                    "api:form-variables",
                    kwargs={"uuid_or_slug": form.uuid},
                ),
                data=data_invalid,
            )

            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

            error = response.json()

            self.assertEqual(error["code"], "invalid")
            self.assertEqual(
                error["invalidParams"][0]["name"],
                "0.key",
            )
            self.assertEqual(
                error["invalidParams"][0]["reason"],
                "Invalid variable key. It must only contain alphanumeric characters, underscores, "
                "dots and dashes and should not be ended by dash or dot.",
            )
            self.assertEqual(
                error["invalidParams"][1]["name"],
                "1.name",
            )
            self.assertEqual(
                error["invalidParams"][1]["code"],
                "blank",
            )

    def test_key_clash_with_static_data(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form)
        form_definition = form_step.form_definition

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "now",
                "name": "Now",
                "source": FormVariableSources.user_defined,
                "data_type": FormVariableDataTypes.string,
                "initial_value": "",
            },
        ]

        self.client.force_authenticate(user)

        with patch(
            "openforms.forms.api.serializers.form_variable.get_static_variables"
        ) as m:
            m.return_value = [
                FormVariable(
                    name="Now",
                    key="now",
                    data_type=FormVariableDataTypes.datetime,
                    initial_value="2021-07-16T21:15:00+00:00",
                )
            ]
            response = self.client.put(
                reverse(
                    "api:form-variables",
                    kwargs={"uuid_or_slug": form.uuid},
                ),
                data=data,
            )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        error = response.json()

        self.assertEqual(error["code"], "invalid")
        self.assertEqual(
            error["invalidParams"][0]["reason"],
            "The variable key cannot be equal to any of the following values: now.",
        )
        self.assertEqual(
            error["invalidParams"][0]["code"],
            "unique",
        )

    def test_key_not_present_in_form_definition(self):
        user = SuperUserFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [{"type": "textfield", "key": "test"}]
            },
        )
        form_definition = form.formstep_set.get().form_definition

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "not-in-configuration",
                "name": "Not in configuration",
                "source": FormVariableSources.component,
                "data_type": FormVariableDataTypes.string,
                "initial_value": "",
            },
        ]

        self.client.force_authenticate(user)

        response = self.client.put(
            reverse(
                "api:form-variables",
                kwargs={"uuid_or_slug": form.uuid},
            ),
            data=data,
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        error = response.json()

        self.assertEqual(error["code"], "invalid")
        self.assertEqual(
            error["invalidParams"][0]["reason"],
            "Invalid component variable: no component with corresponding key present in the form definition.",
        )
        self.assertEqual(
            error["invalidParams"][0]["name"],
            "0.key",
        )
        self.assertEqual(
            error["invalidParams"][0]["code"],
            "invalid",
        )

    def test_data_type_initial_value_set(self):
        user = SuperUserFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {"key": "test1", "type": "textfield", "multiple": False},
                    {
                        "key": "test2",
                        "type": "textfield",
                        "multiple": False,
                        "defaultValue": "test2 default value",
                    },
                    {
                        "key": "test3",
                        "type": "textfield",
                        "multiple": True,
                        "defaultValue": ["test3 default value"],
                    },
                    {
                        "key": "test4",
                        "type": "number",
                        "multiple": False,
                        "defaultValue": 4,
                    },
                ]
            },
        )

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": form.formstep_set.first().form_definition.uuid},
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "test1",
                "name": "Test 1",
                "source": FormVariableSources.component,
                "data_type": FormVariableDataTypes.string,
            },
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "test2",
                "name": "Test 2",
                "source": FormVariableSources.component,
                "data_type": FormVariableDataTypes.string,
            },
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "test3",
                "name": "Test 3",
                "source": FormVariableSources.component,
                "data_type": FormVariableDataTypes.string,  # The backend should set this to the right value (array)
            },
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "test4",
                "name": "Test 4",
                "source": FormVariableSources.component,
                "data_type": FormVariableDataTypes.string,  # The backend should set this to the right value (float)
            },
        ]

        self.client.force_authenticate(user)

        response = self.client.put(
            reverse(
                "api:form-variables",
                kwargs={"uuid_or_slug": form.uuid},
            ),
            data=data,
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        variable1 = form.formvariable_set.get(key="test1")
        variable2 = form.formvariable_set.get(key="test2")
        variable3 = form.formvariable_set.get(key="test3")
        variable4 = form.formvariable_set.get(key="test4")

        self.assertEqual(FormVariableDataTypes.string, variable1.data_type)
        self.assertEqual(FormVariableDataTypes.string, variable2.data_type)
        self.assertEqual(FormVariableDataTypes.array, variable3.data_type)
        self.assertEqual(FormVariableDataTypes.float, variable4.data_type)

        self.assertIsNone(variable1.initial_value)
        self.assertEqual("test2 default value", variable2.initial_value)
        self.assertEqual(["test3 default value"], variable3.initial_value)
        self.assertEqual(4, variable4.initial_value)

    def test_validators_accepts_only_numeric_keys(self):
        user = SuperUserFactory.create()
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {"key": "1", "type": "textfield"},
                ]
            },
        )

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail",
            kwargs={"uuid": form.formstep_set.first().form_definition.uuid},
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "1",
                "name": "Variable 1",
                "source": FormVariableSources.component,
                "data_type": FormVariableDataTypes.string,
            }
        ]

        self.client.force_authenticate(user)

        response = self.client.put(
            reverse(
                "api:form-variables",
                kwargs={"uuid_or_slug": form.uuid},
            ),
            data=data,
        )

        # The variable is considered valid
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_validate_prefill_consistency(self):
        user = SuperUserFactory.create()
        self.client.force_authenticate(user)
        form = FormFactory.create()
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"
        data = [
            {
                "form": form_url,
                "form_definition": "",
                "name": "Variable 1",
                "key": "variable1",
                "source": FormVariableSources.user_defined,
                "dataType": FormVariableDataTypes.string,
                "prefillPlugin": "demo",
                "prefillAttribute": "",
            }
        ]

        response = self.client.put(
            reverse(
                "api:form-variables",
                kwargs={"uuid_or_slug": form.uuid},
            ),
            data=data,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()
        self.assertEqual(error["code"], "invalid")
        self.assertEqual(len(error["invalidParams"]), 1)
        self.assertEqual(
            error["invalidParams"][0]["name"],
            "0.prefillAttribute",
        )

    def test_bulk_create_and_update_with_non_camel_case_initial_values(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user)

        form = FormFactory.create(generate_minimal_setup=True)
        form_definition = form.formstep_set.get().form_definition
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"
        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": form_definition.configuration["components"][0]["key"],
                "name": "Test",
                "service_fetch_configuration": None,
                "data_type": FormVariableDataTypes.object,
                "source": FormVariableSources.component,
                "initial_value": {
                    "VALUE IN UPPERCASE": True,
                    "VALUE-IN-UPPER-KEBAB-CASE": True,
                    "VALUE_IN_UPPER_SNAKE_CASE": False,
                    "value in lower case": False,
                    "value-in-lower-kebab-case": False,
                    "value_in_lower_snake_case": True,
                },
            }
        ]

        response = self.client.put(
            reverse(
                "api:form-variables",
                kwargs={"uuid_or_slug": form.uuid},
            ),
            data=data,
        )

        expected_initial_value = {
            "VALUE IN UPPERCASE": True,
            "VALUE-IN-UPPER-KEBAB-CASE": True,
            "VALUE_IN_UPPER_SNAKE_CASE": False,
            "value in lower case": False,
            "value-in-lower-kebab-case": False,
            "value_in_lower_snake_case": True,
        }

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(expected_initial_value, response.json()[0]["initialValue"])
