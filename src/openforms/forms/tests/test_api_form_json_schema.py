from django.test import override_settings, tag
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.formio.constants import DataSrcOptions
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableDataTypes


@override_settings(LANGUAGE_CODE="en")
class FormJsonSchemaAPITests(APITestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create(is_staff=True)

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_objects_api(self):
        objects_api_group = ObjectsAPIGroupConfigFactory.create()
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "firstName", "type": "textfield", "label": "First Name"},
                    {
                        "key": "last.Name",
                        "type": "textfield",
                        "multiple": True,
                        "label": "Last Name",
                    },
                    {"key": "file", "type": "file", "label": "File", "multiple": False},
                    {
                        "type": "selectboxes",
                        "key": "selectboxes",
                        "values": [
                            {"label": "Option 1", "value": "option1"},
                            {"label": "Option 2", "value": "option2"},
                        ],
                        "dataSrc": DataSrcOptions.manual,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        FormVariableFactory.create(
            form=form,
            name="Foo",
            key="foo",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        FormRegistrationBackendFactory.create(
            key="backend1",
            name="Objects API",
            backend="objects_api",
            form=form,
            options={
                "version": 2,
                "objects_api_group": objects_api_group.identifier,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "transform_to_list": [],
            },
        )

        url = reverse("api:form-json-schema", kwargs={"uuid_or_slug": form.uuid})
        options = {"registration_backend_key": "backend1"}

        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "firstName": {"title": "First Name", "type": "string"},
                "last": {
                    "type": "object",
                    "properties": {
                        "Name": {
                            "title": "Last Name",
                            "type": "array",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["Name"],
                    "additionalProperties": False,
                },
                "file": {
                    "title": "File",
                    "type": "string",
                    "oneOf": [{"format": "uri"}, {"pattern": "^$"}],
                },
                "selectboxes": {
                    "title": "Select boxes",
                    "type": "object",
                    "properties": {
                        "option1": {"type": "boolean"},
                        "option2": {"type": "boolean"},
                    },
                    "required": ["option1", "option2"],
                    "additionalProperties": False,
                },
                "foo": {"type": "array", "title": "Foo"},
            },
            "required": [
                "firstName",
                "last",
                "selectboxes",
                "file",
                "foo",
            ],
            "additionalProperties": False,
        }

        response = self.client.get(url, options)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        schema = response.json()

        # Note: convert the required list to a set to counteract test flakiness. The
        # order of this list can change because we iterate over the variables from the
        # database when generating the schema.
        schema["required"] = set(schema["required"])
        expected_schema["required"] = set(expected_schema["required"])

        self.assertEqual(schema, expected_schema)

    @tag("gh-5464")
    def test_objects_api_incomplete_configuration_options(self):
        # legacy/old forms may have incomplete registration backend options in the
        # database. These are handled through serializer defaults and may not cause
        # crashes.
        objects_api_group = ObjectsAPIGroupConfigFactory.create()
        form_registration_backend = FormRegistrationBackendFactory.create(
            key="backend1",
            name="Objects API",
            backend="objects_api",
            options={
                "objects_api_group": objects_api_group.identifier,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
            },
        )

        url = reverse(
            "api:form-json-schema",
            kwargs={"uuid_or_slug": form_registration_backend.form.uuid},
        )

        response = self.client.get(url, {"registration_backend_key": "backend1"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_generic_json(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "firstName", "type": "textfield", "label": "First Name"},
                    {
                        "key": "last.Name",
                        "type": "textfield",
                        "multiple": True,
                        "label": "Last Name",
                    },
                    {"key": "file", "type": "file", "label": "File", "multiple": False},
                    {
                        "type": "selectboxes",
                        "key": "selectboxes",
                        "values": [
                            {"label": "Option 1", "value": "option1"},
                            {"label": "Option 2", "value": "option2"},
                        ],
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        FormVariableFactory.create(
            form=form,
            name="Foo",
            key="foo",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        FormRegistrationBackendFactory.create(
            key="backend1",
            name="Generic JSON",
            backend="json_dump",
            form=form,
            options={"transform_to_list": []},
        )

        url = reverse("api:form-json-schema", kwargs={"uuid_or_slug": form.uuid})
        options = {"registration_backend_key": "backend1"}

        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "firstName": {"title": "First Name", "type": "string"},
                "last": {
                    "type": "object",
                    "properties": {
                        "Name": {
                            "title": "Last Name",
                            "type": "array",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["Name"],
                    "additionalProperties": False,
                },
                "file": {
                    "title": "File",
                    "type": ["null", "object"],
                    "properties": {
                        "file_name": {"type": "string"},
                        "content": {"type": "string", "format": "base64"},
                    },
                    "required": ["file_name", "content"],
                    "additionalProperties": False,
                },
                "selectboxes": {
                    "title": "Select boxes",
                    "type": "object",
                    "properties": {
                        "option1": {"type": "boolean"},
                        "option2": {"type": "boolean"},
                    },
                    "required": ["option1", "option2"],
                    "additionalProperties": False,
                },
                "foo": {"type": "array", "title": "Foo"},
            },
            "required": [
                "firstName",
                "last",
                "selectboxes",
                "file",
                "foo",
            ],
            "additionalProperties": False,
        }

        response = self.client.get(url, options)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        schema = response.json()

        # Note: convert the required list to a set to counteract test flakiness. The
        # order of this list can change because we iterate over the variables from the
        # database when generating the schema.
        schema["required"] = set(schema["required"])
        expected_schema["required"] = set(expected_schema["required"])

        self.assertEqual(schema, expected_schema)

    def test_backend_that_should_not_allow_schema_generation(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "firstName", "type": "textfield", "label": "First Name"},
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        FormRegistrationBackendFactory.create(
            key="backend1",
            name="Email",
            backend="email",
            form=form,
            options={"to_emails": ["foo@example.com"]},
        )

        url = reverse("api:form-json-schema", kwargs={"uuid_or_slug": form.uuid})
        options = {"registration_backend_key": "backend1"}

        response = self.client.get(url, options)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["invalidParams"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0],
            {
                "name": "registrationBackendKey",
                "code": "invalid",
                "reason": "Backend with id 'email' does not allow JSON schema generation",
            },
        )

    def test_backend_that_does_not_exist(self):
        form = FormFactory.create(name="Form 1")
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "selectboxes",
                        "key": "selectboxes",
                        "values": [
                            {"label": "Option a", "value": "option_a"},
                            {"label": "Option b", "value": "option_b"},
                        ],
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        url = reverse("api:form-json-schema", kwargs={"uuid_or_slug": form.uuid})
        options = {"registration_backend_key": "backend1"}

        response = self.client.get(url, options)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        errors = response.json()["invalidParams"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0],
            {
                "name": "registrationBackendKey",
                "code": "invalid",
                "reason": "Backend with key 'backend1' does not exist for form 'Form 1'",
            },
        )

    def test_properties_should_not_be_converted_to_camel_case(self):
        objects_api_group = ObjectsAPIGroupConfigFactory.create()
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "selectboxes",
                        "key": "selectboxes",
                        "values": [
                            {"label": "Option a", "value": "option_a"},
                            {"label": "Option b", "value": "option_b"},
                        ],
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        FormRegistrationBackendFactory.create(
            key="backend1",
            name="Objects API",
            backend="objects_api",
            form=form,
            options={
                "objects_api_group": objects_api_group.identifier,
                "objecttype": "8e46e0a5-b1b4-449b-b9e9-fa3cea655f48",
                "objecttype_version": 3,
                "version": 2,
                "transform_to_list": [],
            },
        )

        url = reverse("api:form-json-schema", kwargs={"uuid_or_slug": form.uuid})
        options = {"registration_backend_key": "backend1"}

        expected_properties = {
            "selectboxes": {
                "title": "Select boxes",
                "type": "object",
                "properties": {
                    "option_a": {"type": "boolean"},
                    "option_b": {"type": "boolean"},
                },
                "required": ["option_a", "option_b"],
                "additionalProperties": False,
            },
        }

        response = self.client.get(url, options)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        schema = response.json()

        self.assertEqual(schema["properties"], expected_properties)
