from django.test import TestCase

from openforms.formio.constants import DataSrcOptions
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..json_schema import generate_json_schema


class GenerateJsonSchemaTests(TestCase):
    def test_correct_variables_included_in_schema(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "firstName", "type": "textfield", "label": "First Name"},
                    {
                        "key": "lastName",
                        "type": "textfield",
                        "multiple": True,
                        "label": "Last Name",
                    },
                    {
                        "label": "Select",
                        "key": "select",
                        "data": {
                            "values": [
                                {"label": "A", "value": "a"},
                                {"label": "B", "value": "b"},
                            ],
                            "dataSrc": DataSrcOptions.manual,
                            "json": "",
                            "url": "",
                            "resource": "",
                            "custom": "",
                        },
                        "type": "select",
                        "multiple": True,
                    },
                    {
                        "type": "selectboxes",
                        "key": "selectboxes",
                        "values": [
                            {"label": "Option 1", "value": "option1"},
                            {"label": "Option 2", "value": "option2"},
                        ],
                    },
                    {
                        "label": "Radio",
                        "key": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
                        "dataSrc": DataSrcOptions.manual,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        form_def_2 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "file",
                        "type": "file",
                        "label": "File",
                        "validate": {"required": True},
                    },
                    {
                        "key": "notIncluded",
                        "type": "textfield",
                        "label": "Not included text field",
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_2)

        FormVariableFactory.create(
            form=form,
            name="Foo",
            key="foo",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        vars_to_include = (
            "firstName",
            "lastName",
            "select",
            "selectboxes",
            "radio",
            "file",
            "auth_bsn",
            "today",
            "foo",
        )
        schema = generate_json_schema(form, vars_to_include)

        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "today": {"title": "Today's date", "type": "string", "format": "date"},
                "auth_bsn": {
                    "title": "BSN",
                    "description": "Uniquely identifies the authenticated person. This value follows the rules for Dutch social security numbers.",
                    "type": "string",
                    "pattern": "^\\d{9}$",
                    "format": "nl-bsn",
                },
                "firstName": {"title": "First Name", "type": "string"},
                "lastName": {
                    "title": "Last Name",
                    "type": "array",
                    "items": {"type": "string"},
                },
                "select": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["a", "b", ""]},
                    "title": "Select",
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
                "radio": {"title": "Radio", "type": "string", "enum": ["a", "b", ""]},
                "file": {
                    "title": "File",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "originalName": {"type": "string"},
                            "size": {"type": "number", "description": "Size in bytes"},
                            "storage": {"type": "string"},
                            "type": {"type": "string"},
                            "url": {"type": "string", "format": "uri"},
                            "data": {
                                "type": "object",
                                "properties": {
                                    "baseUrl": {"type": "string", "format": "uri"},
                                    "form": {"type": "string"},
                                    "name": {"type": "string"},
                                    "project": {"type": "string"},
                                    "size": {
                                        "type": "number",
                                        "description": "Size in bytes",
                                    },
                                    "url": {"type": "string", "format": "uri"},
                                },
                                "required": [
                                    "baseUrl",
                                    "form",
                                    "name",
                                    "project",
                                    "size",
                                    "url",
                                ],
                            },
                        },
                        "required": [
                            "name",
                            "originalName",
                            "size",
                            "storage",
                            "type",
                            "url",
                            "data",
                        ],
                    },
                },
                "foo": {"type": "array", "title": "Foo"},
            },
            "required": (
                "firstName",
                "lastName",
                "select",
                "selectboxes",
                "radio",
                "file",
                "auth_bsn",
                "today",
                "foo",
            ),
            "additionalProperties": False,
        }

        self.assertEqual(schema, expected_schema)


class FormVariableAsJsonSchemaTests(TestCase):

    def test_component(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Foo",
                        "source": FormVariableSources.component,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        var = form_def.formvariable_set.first()
        schema = var.as_json_schema()

        expected_schema = {"title": "Foo", "type": "string"}
        self.assertEqual(schema, expected_schema)

    def test_user_defined(self):
        var = FormVariableFactory.create(
            name="Foo",
            key="foo",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        schema = var.as_json_schema()

        expected_schema = {"title": "Foo", "type": "array"}
        self.assertEqual(schema, expected_schema)

    def test_schema_assigned_manually(self):
        var = FormVariableFactory.create(
            name="Foo",
            key="foo",
            data_type=FormVariableDataTypes.object,
            initial_value={"foo": "bar"},
        )
        var.json_schema = {"type": "string"}

        schema = var.as_json_schema()

        expected_schema = {"type": "string"}
        self.assertEqual(schema, expected_schema)
