from django.test import TestCase, tag

from zgw_consumers.constants import AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.formio.constants import DataSrcOptions
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin
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
                        "defaultValue": [],
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
                        "defaultValue": [],
                    },
                    {
                        "type": "selectboxes",
                        "key": "selectboxes",
                        "label": "Select boxes",
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
                        "file": {"type": []},
                        "filePattern": "",
                        "url": "",
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

        expected_properties = {
            "today": {"title": "Today's date", "type": "string", "format": "date"},
            "auth_bsn": {
                "title": "BSN",
                "description": "Uniquely identifies the authenticated person. This value follows the rules for Dutch social security numbers.",
                "type": "string",
                "pattern": "^\\d{9}$|^$",
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
        }
        expected_required = {
            "today",
            "auth_bsn",
            "firstName",
            "lastName",
            "select",
            "selectboxes",
            "radio",
            "file",
            "foo",
        }

        with self.subTest("properties"):
            self.assertEqual(schema["properties"], expected_properties)

        with self.subTest("required"):
            self.assertEqual(set(schema["required"]), expected_required)

    @tag("gh-5205")
    def test_non_existing_variable_not_in_required(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"key": "firstName", "type": "textfield", "label": "First Name"},
                    {"key": "lastName", "type": "textfield", "label": "Last Name"},
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        vars_to_include = ("firstName", "lastName", "nonExistingVariable")
        schema = generate_json_schema(form, vars_to_include)

        self.assertEqual(schema["required"], ["firstName", "lastName"])

    def test_key_with_period(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "nested.data",
                        "type": "textfield",
                        "label": "Textfield with nested data",
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        schema = generate_json_schema(form, limit_to_variables=["nested.data"])

        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "nested": {
                    "properties": {
                        "data": {
                            "title": "Textfield with nested data",
                            "type": "string",
                        }
                    },
                    "required": ["data"],
                    "type": "object",
                    "additionalProperties": False,
                },
            },
            "required": ["nested"],
            "additionalProperties": False,
        }
        self.assertEqual(schema, expected_schema)

    def test_key_with_two_periods(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "nested.data.second",
                        "type": "textfield",
                        "label": "Textfield with nested data",
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        schema = generate_json_schema(form, limit_to_variables=["nested.data.second"])

        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "nested": {
                    "properties": {
                        "data": {
                            "properties": {
                                "second": {
                                    "title": "Textfield with nested data",
                                    "type": "string",
                                }
                            },
                            "required": ["second"],
                            "type": "object",
                            "additionalProperties": False,
                        }
                    },
                    "required": ["data"],
                    "type": "object",
                    "additionalProperties": False,
                },
            },
            "required": ["nested"],
            "additionalProperties": False,
        }
        self.assertEqual(schema, expected_schema)

    def test_two_keys_with_same_top_level(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "nested.key_1",
                        "type": "textfield",
                        "label": "Textfield with nested data",
                    },
                    {
                        "key": "nested.key_2",
                        "type": "textfield",
                        "label": "Textfield 2 with nested data",
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        schema = generate_json_schema(
            form, limit_to_variables=["nested.key_1", "nested.key_2"]
        )

        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "nested": {
                    "properties": {
                        "key_1": {
                            "title": "Textfield with nested data",
                            "type": "string",
                        },
                        "key_2": {
                            "title": "Textfield 2 with nested data",
                            "type": "string",
                        },
                    },
                    "required": ["key_1", "key_2"],
                    "type": "object",
                    "additionalProperties": False,
                },
            },
            "required": ["nested"],
            "additionalProperties": False,
        }
        self.assertEqual(schema, expected_schema)

    def test_nested_data_in_edit_grid(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "label": "Edit grid",
                        "key": "editgrid",
                        "type": "editgrid",
                        "groupLabel": "item",
                        "components": [
                            {
                                "label": "Text field A",
                                "key": "text.a",
                                "type": "textfield",
                            },
                            {
                                "label": "Text field B",
                                "key": "text.b",
                                "type": "textfield",
                            },
                            {
                                "label": "Email",
                                "key": "email",
                                "type": "email",
                            },
                        ],
                    }
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        schema = generate_json_schema(form, limit_to_variables=["editgrid"])

        expected_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "editgrid": {
                    "title": "Edit grid",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "object",
                                "properties": {
                                    "a": {"title": "Text field A", "type": "string"},
                                    "b": {"title": "Text field B", "type": "string"},
                                },
                                "additionalProperties": False,
                                "required": ["a", "b"],
                            },
                            "email": {
                                "title": "Email",
                                "type": "string",
                                "format": "email",
                            },
                        },
                        "additionalProperties": False,
                        "required": ["text", "email"],
                    },
                },
            },
            "required": ["editgrid"],
            "additionalProperties": False,
        }

        self.assertEqual(schema, expected_schema)

    def test_user_variable_as_data_source(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "label": "Select",
                        "key": "select",
                        "type": "select",
                        "openForms": {
                            "dataSrc": DataSrcOptions.variable,
                            "itemsExpression": {"var": "valuesForComponents"},
                        },
                        "data": {
                            "values": [],
                            "json": "",
                            "url": "",
                            "resource": "",
                            "custom": "",
                        },
                    },
                    {
                        "label": "Select boxes",
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "openForms": {
                            "dataSrc": DataSrcOptions.variable,
                            "itemsExpression": {"var": "valuesForComponents"},
                        },
                        "values": [],
                    },
                    {
                        "label": "Radio",
                        "key": "radio",
                        "type": "radio",
                        "openForms": {
                            "dataSrc": DataSrcOptions.variable,
                            "itemsExpression": {"var": "valuesForComponents"},
                        },
                        "values": [],
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        FormVariableFactory.create(
            form=form,
            name="Values for components",
            key="valuesForComponents",
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            initial_value=["A", "B", "C"],
        )

        schema = generate_json_schema(
            form, limit_to_variables=["select", "selectboxes", "radio"]
        )

        with self.subTest("select"):
            self.assertEqual(
                schema["properties"]["select"]["enum"], ["A", "B", "C", ""]
            )

        with self.subTest("selectboxes"):
            expected_property = {
                "title": "Select boxes",
                "type": "object",
                "properties": {
                    "A": {"type": "boolean"},
                    "B": {"type": "boolean"},
                    "C": {"type": "boolean"},
                },
                "required": ["A", "B", "C"],
                "additionalProperties": False,
            }
            self.assertEqual(schema["properties"]["selectboxes"], expected_property)

        with self.subTest("radio"):
            self.assertEqual(schema["properties"]["radio"]["enum"], ["A", "B", "C", ""])


class GenerateJsonSchemaReferenceListsTests(OFVCRMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.reference_lists_service = ServiceFactory.create(
            api_root="http://localhost:8004/api/v1/",
            slug="reference_lists",
            auth_type=AuthTypes.no_auth,
        )

    def setUp(self):
        super().setUp()
        self.addCleanup(clear_caches)

    def test_select_with_reference_list_as_data_source(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "label": "Select",
                        "key": "select",
                        "type": "select",
                        "openForms": {
                            "code": "tabel1",
                            "dataSrc": DataSrcOptions.reference_lists,
                            "service": "reference_lists",
                        },
                        "data": {
                            "values": [],
                            "json": "",
                            "url": "",
                            "resource": "",
                            "custom": "",
                        },
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        schema = generate_json_schema(form, limit_to_variables=["select"])

        self.assertEqual(
            schema["properties"]["select"]["enum"], ["option2", "option1", ""]
        )

    def test_select_boxes_with_reference_list_as_data_source(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "label": "Select boxes",
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "openForms": {
                            "code": "tabel1",
                            "dataSrc": DataSrcOptions.reference_lists,
                            "service": "reference_lists",
                        },
                        "values": [],
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        schema = generate_json_schema(form, limit_to_variables=["selectboxes"])

        expected_property = {
            "title": "Select boxes",
            "type": "object",
            "properties": {
                "option2": {"type": "boolean"},
                "option1": {"type": "boolean"},
            },
            "required": ["option2", "option1"],
            "additionalProperties": False,
        }
        self.assertEqual(schema["properties"]["selectboxes"], expected_property)

    def test_radio_with_reference_list_as_data_source(self):
        form = FormFactory.create()
        form_def_1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "label": "Radio",
                        "key": "radio",
                        "type": "radio",
                        "openForms": {
                            "code": "tabel1",
                            "dataSrc": DataSrcOptions.reference_lists,
                            "service": "reference_lists",
                        },
                        "values": [],
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def_1)

        schema = generate_json_schema(form, limit_to_variables=["radio"])

        self.assertEqual(
            schema["properties"]["radio"]["enum"], ["option2", "option1", ""]
        )


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
