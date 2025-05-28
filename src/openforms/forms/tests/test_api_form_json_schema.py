from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.formio.constants import DataSrcOptions
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableDataTypes


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

        url = reverse("api:form-json-schema", kwargs={"uuid_or_slug": form.uuid})
        options = {"registration_plugin_id": "objects_api"}

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
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "option1": {"type": "boolean"},
                                "option2": {"type": "boolean"},
                            },
                            "required": ["option1", "option2"],
                            "additionalProperties": False,
                        },
                        {
                            "type": "array",
                            "items": {"type": "string", "enum": ["option1", "option2"]},
                        },
                    ],
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
        # DB when generating the schema.
        schema["required"] = set(schema["required"])
        expected_schema["required"] = set(expected_schema["required"])

        self.assertEqual(schema, expected_schema)

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

        url = reverse("api:form-json-schema", kwargs={"uuid_or_slug": form.uuid})
        options = {"registration_plugin_id": "json_dump"}

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
                        # TODO-5312: I would want this to be 'file_name', but it is
                        #  converted to 'fileName'
                        "file_name": {"type": "string"},
                        "content": {"type": "string", "format": "base64"},
                    },
                    "required": ["file_name", "content"],
                    "additionalProperties": False,
                },
                "selectboxes": {
                    "title": "Select boxes",
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "option1": {"type": "boolean"},
                                "option2": {"type": "boolean"},
                            },
                            "required": ["option1", "option2"],
                            "additionalProperties": False,
                        },
                        {
                            "type": "array",
                            "items": {"type": "string", "enum": ["option1", "option2"]},
                        },
                    ],
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
        # DB when generating the schema.
        schema["required"] = set(schema["required"])
        expected_schema["required"] = set(expected_schema["required"])

        self.assertEqual(schema, expected_schema)

    def test_plugin_that_should_not_allow_schema_generation(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "firstName", "type": "textfield", "label": "First Name"},
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        url = reverse("api:form-json-schema", kwargs={"uuid_or_slug": form.uuid})
        options = {"registration_plugin_id": "email"}

        response = self.client.get(url, options)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
