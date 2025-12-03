from unittest.mock import patch

from django.test import override_settings, tag
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)
from openforms.contrib.customer_interactions.tests.factories import (
    CustomerInteractionsAPIGroupConfigFactory,
)
from openforms.forms.models import FormVariable
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.prefill.contrib.customer_interactions.plugin import (
    PLUGIN_IDENTIFIER as COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
)
from openforms.prefill.contrib.demo.plugin import DemoPrefill
from openforms.prefill.tests.utils import get_test_register, patch_prefill_registry
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

    def test_it_accepts_inline_service_fetch_configs(self):
        designer = StaffUserFactory.create(user_permissions=["change_form"])
        service = ServiceFactory.create(
            api_type=APITypes.orc,
            api_root="http://testserver/api/v2",
            auth_type=AuthTypes.no_auth,
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

    def test_bulk_create_and_update_with_prefill_constraints(self):
        # Isolate the prefill registry/plugins for this test - we care about the pattern,
        # not about particular plugin implementation details
        new_register = get_test_register()

        class OptionsSerializer(serializers.Serializer):
            foo = serializers.CharField(required=True, allow_blank=False)

        class OptionsPrefill(DemoPrefill):
            options = OptionsSerializer

        new_register("demo-options")(OptionsPrefill)

        # set up registry patching for the test
        cm = patch_prefill_registry(new_register)
        cm.__enter__()
        self.addCleanup(lambda: cm.__exit__(None, None, None))

        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user)

        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form)
        form_definition = form_step.form_definition
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"
        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        with self.subTest("component source with prefill options"):
            data = [
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "key": form_definition.configuration["components"][0]["key"],
                    "name": "Test",
                    "service_fetch_configuration": None,
                    "data_type": FormVariableDataTypes.string,
                    "source": FormVariableSources.component,
                    "prefill_options": {
                        "variables_mapping": [
                            {"variable_key": "data", "target_path": ["test"]}
                        ]
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

            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
            self.assertEqual(response.json()["invalidParams"][0]["code"], "invalid")
            self.assertEqual(
                response.json()["invalidParams"][0]["reason"],
                _("Prefill options should not be specified for component variables."),
            )

        with self.subTest(
            "component source with prefill attribute and not prefill plugin"
        ):
            data = [
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "key": form_definition.configuration["components"][0]["key"],
                    "name": "Test",
                    "service_fetch_configuration": None,
                    "data_type": FormVariableDataTypes.string,
                    "source": FormVariableSources.component,
                    "prefill_attribute": "test",
                }
            ]

            response = self.client.put(
                reverse(
                    "api:form-variables",
                    kwargs={"uuid_or_slug": form.uuid},
                ),
                data=data,
            )

            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
            self.assertEqual(response.json()["invalidParams"][0]["code"], "invalid")
            self.assertEqual(
                response.json()["invalidParams"][0]["reason"],
                _(
                    "Prefill plugin must be specified with either prefill attribute or prefill options."
                ),
            )

        with self.subTest(
            "both sources with prefill plugin, prefill attribute and prefill options"
        ):
            data = [
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "key": form_definition.configuration["components"][0]["key"],
                    "name": "Test",
                    "service_fetch_configuration": None,
                    "data_type": FormVariableDataTypes.string,
                    "source": FormVariableSources.user_defined,
                    "prefill_plugin": "demo",
                    "prefill_attribute": "test",
                    "prefill_options": {
                        "variables_mapping": [
                            {"variable_key": "data", "target_path": ["test"]}
                        ]
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

            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
            self.assertEqual(response.json()["invalidParams"][0]["code"], "invalid")
            self.assertEqual(
                response.json()["invalidParams"][0]["reason"],
                _(
                    "Prefill plugin, attribute and options can not be specified at the same time."
                ),
            )

        with self.subTest(
            "user_defined with prefill plugin and prefill options is allowed"
        ):
            data = [
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "key": "userdefined",
                    "name": "Test",
                    "service_fetch_configuration": None,
                    "data_type": FormVariableDataTypes.string,
                    "source": FormVariableSources.user_defined,
                    "prefill_plugin": "demo-options",
                    "prefill_attribute": "",
                    "prefill_options": {"foo": "bar"},
                }
            ]

            response = self.client.put(
                reverse(
                    "api:form-variables",
                    kwargs={"uuid_or_slug": form.uuid},
                ),
                data=data,
            )

            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_bulk_create_and_update_with_non_camel_case_initial_values(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user)

        form = FormFactory.create()
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"

        data = [
            {
                "form": form_url,
                "form_definition": None,
                "key": "someKey",
                "source": FormVariableSources.user_defined,
                "name": "Test",
                "service_fetch_configuration": None,
                "data_type": FormVariableDataTypes.object,
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

    @tag("gh-5058", "gh-4824")
    def test_form_variables_state_after_step_and_variables_submitted(self):
        """
        Test that form variables are left in a consistent state at the end.

        Form variables for each step are managed by the step create/update endpoint.
        After those have been submitted, the (user) defined variables are submitted,
        and this call is used to bring everything in a resolved consistent state,
        without any celery tasks as those lead to race conditions and deadlocks.

        Step variables submitted to this endpoint must be ignored, obsolete step
        variables must be removed and user defined variables must be created or
        updated.
        """
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user)
        random_fd = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "floating",
                        "type": "textfield",
                        "label": "Floating",
                    }
                ]
            }
        )
        # start with a form with a single step
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "toBeRemoved",
                        "label": "To be removed",
                    },
                    {
                        "type": "date",
                        "key": "toBeUpdated",
                        "label": "To be updated",
                    },
                ]
            },
        )
        FormVariable.objects.create(
            form=form,
            source=FormVariableSources.component,
            form_definition=random_fd,
            key="floating",
        )
        FormVariableFactory.create(
            form=form,
            user_defined=True,
            key="staleUserDefined",
        )
        assert set(form.formvariable_set.values_list("key", flat=True)) == {
            "toBeRemoved",
            "toBeUpdated",
            "floating",
            "staleUserDefined",
        }
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_endpoint = f"http://testserver{form_path}"
        step_1 = form.formstep_set.get()
        # new form definition for step 1
        fd1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "toBeUpdated",
                        "label": "To be updated",
                    }
                ]
            }
        )
        fd1_detail_url = reverse("api:formdefinition-detail", kwargs={"uuid": fd1.uuid})
        # new form definition for new second step
        fd2 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "toBeCreated",
                        "label": "To be created",
                    }
                ]
            }
        )
        fd2_detail_url = reverse("api:formdefinition-detail", kwargs={"uuid": fd2.uuid})

        # simulate the calls made by the frontend, and to humour the chaos of real
        # networks, do them out of order.
        create_step_endpoint = reverse(
            "api:form-steps-list", kwargs={"form_uuid_or_slug": form.uuid}
        )
        with self.subTest("create step 2"):
            response_1 = self.client.post(
                create_step_endpoint,
                data={
                    "formDefinition": f"http://testserver{fd2_detail_url}",
                    "index": 1,
                },
            )
            self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)
        with self.subTest("update step 1"):
            endpoint_2 = reverse(
                "api:form-steps-detail",
                kwargs={
                    "form_uuid_or_slug": form.uuid,
                    "uuid": step_1.uuid,
                },
            )
            self.client.delete(endpoint_2)
            response_2 = self.client.post(
                create_step_endpoint,
                data={
                    "formDefinition": f"http://testserver{fd1_detail_url}",
                    "index": 1,
                },
            )
            self.assertEqual(response_2.status_code, status.HTTP_201_CREATED)
        with self.subTest("push form variables"):
            variables = [
                # step variables - must be ignored
                {
                    "form": form_endpoint,
                    "form_definition": f"http://testserver{fd1_detail_url}",
                    "key": "toBeUpdated",
                    "name": "Ignore me",
                    "data_type": FormVariableDataTypes.string,
                    "source": FormVariableSources.component,
                    "initial_value": "ignore me",
                },
                {
                    "form": form_endpoint,
                    "form_definition": f"http://testserver{fd2_detail_url}",
                    "key": "toBeCreated",
                    "name": "Ignore me",
                    "data_type": FormVariableDataTypes.date,
                    "source": FormVariableSources.component,
                    "initial_value": "ignore me",
                },
                # user defined - must be created
                {
                    "form": form_endpoint,
                    "form_definition": "",
                    "key": "userDefined",
                    "name": "User defined",
                    "data_type": FormVariableDataTypes.array,
                    "source": FormVariableSources.user_defined,
                    "initial_value": ["foo"],
                },
            ]

            response = self.client.put(
                reverse(
                    "api:form-variables",
                    kwargs={"uuid_or_slug": form.uuid},
                ),
                data=variables,
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest("assert variables state"):
            form_variables = {
                variable.key: variable for variable in form.formvariable_set.all()
            }
            # one from step 1, one from step 2 and one user defined variable
            self.assertEqual(len(form_variables), 1 + 1 + 1)

            self.assertIn("toBeUpdated", form_variables)
            to_be_updated = form_variables["toBeUpdated"]
            self.assertEqual(to_be_updated.form_definition, fd1)
            self.assertEqual(to_be_updated.name, "To be updated")
            self.assertEqual(to_be_updated.data_type, FormVariableDataTypes.float)
            self.assertNotEqual(to_be_updated.initial_value, "ignore me")

            self.assertIn("toBeCreated", form_variables)
            to_be_created = form_variables["toBeCreated"]
            self.assertEqual(to_be_created.form_definition, fd2)
            self.assertEqual(to_be_created.name, "To be created")
            self.assertEqual(to_be_created.data_type, FormVariableDataTypes.string)
            self.assertNotEqual(to_be_created.initial_value, "ignore me")

            self.assertNotIn("toBeRemoved", form_variables)

            self.assertIn("userDefined", form_variables)
            user_defined = form_variables["userDefined"]
            self.assertIsNone(user_defined.form_definition)
            self.assertEqual(user_defined.name, "User defined")
            self.assertEqual(user_defined.data_type, FormVariableDataTypes.array)
            self.assertEqual(user_defined.initial_value, ["foo"])

    @tag("gh-5142")
    def test_api_call_returns_all_variables(self):
        """
        Assert that the api endpoint returns list of all variables.

        This bug was introduced with the fix for GH-5058 (commit d86a1bbd), where
        FormVariableListSerializer no longer processes component variables. This means
        that after saving the serializer, `serializer.data` only contains user-defined
        variables, and we have to ensure it returns all form variables with another
        serializer.
        """
        user = SuperUserFactory.create()
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                    },
                    {
                        "type": "date",
                        "key": "date",
                    },
                ]
            },
        )
        form_definition = form_step.form_definition

        FormVariableFactory.create(
            form=form,
            name="User defined",
            key="userDefined",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
        )

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver{form_path}"

        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver{form_definition_path}"

        data = [
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "textfield",
                "name": "textfield",
                "source": FormVariableSources.component,
                "data_type": FormVariableDataTypes.string,
                "initial_value": "",
                "service_fetch_configuration": None,
            },
            {
                "form": form_url,
                "form_definition": form_definition_url,
                "key": "date",
                "name": "date",
                "source": FormVariableSources.component,
                "data_type": FormVariableDataTypes.string,
                "initial_value": "",
                "service_fetch_configuration": None,
            },
            {
                "form": form_url,
                "form_definition": "",
                "key": "userDefined",
                "name": "User defined",
                "data_type": FormVariableDataTypes.array,
                "source": FormVariableSources.user_defined,
                "initial_value": ["foo"],
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
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)


@override_settings(LANGUAGE_CODE="en")
class CommunicationPreferencesPrefillPluginFormVariableViewsetTest(APITestCase):
    def test_bulk_create_and_update_with_profile_form_variables(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user)

        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "customerProfile",
                        "key": "profile",
                        "name": "Profile",
                        "digitalAddressTypes": ["email"],
                        "shouldUpdateCustomerData": True,
                    },
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield",
                    },
                ]
            },
        )
        form_definition = form_step.form_definition
        customer_interactions_api = CustomerInteractionsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"
        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"

        with self.subTest(
            "Create variable with textfield component as `profile form variable`"
        ):
            data = [
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "key": "profile",
                    "name": "Profile",
                    "data_type": FormVariableDataTypes.array,
                    "source": FormVariableSources.component,
                },
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "key": "textfield",
                    "name": "Textfield",
                    "data_type": FormVariableDataTypes.string,
                    "source": FormVariableSources.component,
                },
                {
                    "name": "profile-prefill",
                    "key": "profilePrefill",
                    "formDefinition": "",
                    "source": FormVariableSources.user_defined,
                    "prefillPlugin": COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
                    "prefillAttribute": "",
                    "prefillIdentifierRole": "main",
                    "dataType": FormVariableDataTypes.string,
                    "prefillOptions": {
                        "customerInteractionsApiGroup": customer_interactions_api.identifier,
                        "profileFormVariable": "textfield",
                    },
                    "form": form_url,
                },
            ]

            response = self.client.put(
                reverse(
                    "api:form-variables",
                    kwargs={"uuid_or_slug": form.uuid},
                ),
                data=data,
            )

            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

            # The error message is targeted at the prefillOptions of the user-defined variable
            self.assertEqual(
                response.json()["invalidParams"][0]["name"],
                "2.prefillOptions.profileFormVariable",
            )
            self.assertEqual(response.json()["invalidParams"][0]["code"], "invalid")
            self.assertEqual(
                response.json()["invalidParams"][0]["reason"],
                _(
                    "Only variables of 'profile' components are allowed as profile form variable."
                ),
            )

        with self.subTest(
            "Create variable with profile component as `profile form variable`"
        ):
            data = [
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "key": "profile",
                    "name": "Profile",
                    "data_type": FormVariableDataTypes.array,
                    "source": FormVariableSources.component,
                },
                {
                    "form": form_url,
                    "form_definition": form_definition_url,
                    "key": "textfield",
                    "name": "Textfield",
                    "data_type": FormVariableDataTypes.string,
                    "source": FormVariableSources.component,
                },
                {
                    "name": "profile-prefill",
                    "key": "profilePrefill",
                    "formDefinition": "",
                    "source": FormVariableSources.user_defined,
                    "prefillPlugin": COMMUNICATION_PREFERENCES_PLUGIN_IDENTIFIER,
                    "prefillAttribute": "",
                    "prefillIdentifierRole": "main",
                    "dataType": FormVariableDataTypes.string,
                    "prefillOptions": {
                        "customerInteractionsApiGroup": customer_interactions_api.identifier,
                        "profileFormVariable": "profile",
                    },
                    "form": form_url,
                },
            ]

            response = self.client.put(
                reverse(
                    "api:form-variables",
                    kwargs={"uuid_or_slug": form.uuid},
                ),
                data=data,
            )

            self.assertEqual(status.HTTP_200_OK, response.status_code)
