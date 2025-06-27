from uuid import UUID

from django.test import TestCase

from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

from ..contrib.generic_json.typing import GenericJSONOptions
from ..contrib.objects_api.typing import RegistrationOptionsV2
from ..service import InvalidBackendIdError, process_variable_schema


class ProcessVariableSchemaTests(TestCase):
    def test_non_existing_backend(self):
        component = {
            "type": "textfield",
            "key": "textfield",
            "label": "textfield",
        }
        with self.assertRaises(InvalidBackendIdError):
            process_variable_schema(component, {}, "non_existing_backend", {})

    def test_backend_that_should_not_allow_schema_generation(self):
        component = {
            "type": "textfield",
            "key": "textfield",
            "label": "textfield",
        }
        with self.assertRaises(InvalidBackendIdError):
            process_variable_schema(
                component, {}, "email", {"to_emails": ["foo@example.com"]}
            )


class ProcessVariableSchemaObjectsApiTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.objects_api_group = ObjectsAPIGroupConfigFactory.create()
        cls.options: RegistrationOptionsV2 = {
            "objects_api_group": cls.objects_api_group,
            "objecttype": UUID("ef7fae29-cb2b-4458-827a-8d5bf9aaa356"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "version": 2,
            "variables_mapping": [],
            "transform_to_list": [],
        }

    def test_file(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "file",
                        "label": "file",
                        "storage": "url",
                        "url": "",
                        "useConfigFiletypes": False,
                        "filePattern": "",
                        "file": {"allowedTypesLabels": []},
                        "multiple": False,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        component = form_def.configuration_wrapper["file"]
        var = form.formvariable_set.get(key="file")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "objects_api", self.options)

        expected_schema = {
            "title": "file",
            "type": "string",
            "oneOf": [{"format": "uri"}, {"pattern": "^$"}],
        }

        self.assertEqual(schema, expected_schema)

    def test_file_multiple(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "file_multiple",
                        "label": "file multiple",
                        "storage": "url",
                        "url": "",
                        "useConfigFiletypes": False,
                        "filePattern": "",
                        "file": {"allowedTypesLabels": []},
                        "multiple": True,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        component = form_def.configuration_wrapper["file_multiple"]
        var = form.formvariable_set.get(key="file_multiple")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "objects_api", self.options)

        expected_schema = {
            "title": "file multiple",
            "type": "array",
            "items": {"type": "string", "format": "uri"},
        }

        self.assertEqual(schema, expected_schema)

    def test_selectboxes(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "label": "Selectboxes",
                        "values": [
                            {"label": "a", "value": "a"},
                            {"label": "b", "value": "b"},
                        ],
                        "validate": {"required": False},
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        component = form_def.configuration_wrapper["selectboxes"]
        var = form.formvariable_set.get(key="selectboxes")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "objects_api", self.options)

        expected_schema = {
            "title": "Selectboxes",
            "type": "object",
            "properties": {
                "a": {"type": "boolean"},
                "b": {"type": "boolean"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        }

        self.assertEqual(schema, expected_schema)

    def test_selectboxes_as_list(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "selectboxes_as_list",
                        "type": "selectboxes",
                        "label": "Selectboxes as list",
                        "values": [
                            {"label": "a", "value": "a"},
                            {"label": "b", "value": "b"},
                        ],
                        "validate": {"required": False},
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        options: RegistrationOptionsV2 = {
            "objects_api_group": self.objects_api_group,
            "objecttype": UUID("ef7fae29-cb2b-4458-827a-8d5bf9aaa356"),
            "objecttype_version": 1,
            "update_existing_object": False,
            "auth_attribute_path": [],
            "iot_submission_report": "",
            "iot_submission_csv": "",
            "iot_attachment": "",
            "version": 2,
            "variables_mapping": [],
            "transform_to_list": ["selectboxes_as_list"],
        }

        component = form_def.configuration_wrapper["selectboxes_as_list"]
        var = form.formvariable_set.get(key="selectboxes_as_list")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "objects_api", options)

        expected_schema = {
            "title": "Selectboxes as list",
            "type": "array",
            "items": {"type": "string", "enum": ["a", "b"]},
        }

        self.assertEqual(schema, expected_schema)

    def test_edit_grid(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "editgrid",
                        "type": "editgrid",
                        "label": "Editgrid",
                        "components": [
                            {
                                "type": "file",
                                "key": "file",
                                "label": "file",
                                "storage": "url",
                                "url": "",
                                "useConfigFiletypes": False,
                                "filePattern": "",
                                "file": {"allowedTypesLabels": []},
                                "multiple": False,
                            },
                            {
                                "type": "file",
                                "key": "file_multiple",
                                "label": "file multiple",
                                "storage": "url",
                                "url": "",
                                "useConfigFiletypes": False,
                                "filePattern": "",
                                "file": {"allowedTypesLabels": []},
                                "multiple": True,
                            },
                            {
                                "key": "selectboxes",
                                "type": "selectboxes",
                                "label": "Selectboxes",
                                "values": [
                                    {"label": "a", "value": "a"},
                                    {"label": "b", "value": "b"},
                                ],
                                "validate": {"required": False},
                            },
                        ],
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        component = form_def.configuration_wrapper["editgrid"]
        var = form.formvariable_set.get(key="editgrid")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "objects_api", self.options)

        expected_schema = {
            "title": "Editgrid",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "title": "file",
                        "oneOf": [{"format": "uri"}, {"pattern": "^$"}],
                    },
                    "file_multiple": {
                        "type": "array",
                        "title": "file multiple",
                        "items": {"format": "uri", "type": "string"},
                    },
                    "selectboxes": {
                        "title": "Selectboxes",
                        "type": "object",
                        "properties": {
                            "a": {"type": "boolean"},
                            "b": {"type": "boolean"},
                        },
                        "required": ["a", "b"],
                        "additionalProperties": False,
                    },
                },
                "required": ["file", "file_multiple", "selectboxes"],
                "additionalProperties": False,
            },
        }

        self.assertEqual(schema, expected_schema)


class ProcessVariableSchemaGenericJsonTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.service = ServiceFactory.create()
        cls.options: GenericJSONOptions = {
            "service": cls.service,
            "path": "",
            "variables": [],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
            "transform_to_list": [],
        }

    def test_file(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "file",
                        "label": "file",
                        "storage": "url",
                        "url": "",
                        "useConfigFiletypes": False,
                        "filePattern": "",
                        "file": {"allowedTypesLabels": []},
                        "multiple": False,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        component = form_def.configuration_wrapper["file"]
        var = form.formvariable_set.get(key="file")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "json_dump", self.options)

        expected_schema = {
            "title": "file",
            "type": ["null", "object"],
            "properties": {
                "file_name": {"type": "string"},
                "content": {"type": "string", "format": "base64"},
            },
            "required": ["file_name", "content"],
            "additionalProperties": False,
        }

        self.assertEqual(schema, expected_schema)

    def test_file_multiple(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "file_multiple",
                        "label": "file multiple",
                        "storage": "url",
                        "url": "",
                        "useConfigFiletypes": False,
                        "filePattern": "",
                        "file": {"allowedTypesLabels": []},
                        "multiple": True,
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        component = form_def.configuration_wrapper["file_multiple"]
        var = form.formvariable_set.get(key="file_multiple")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "json_dump", self.options)

        expected_schema = {
            "title": "file multiple",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string"},
                    "content": {"type": "string", "format": "base64"},
                },
                "required": ["file_name", "content"],
                "additionalProperties": False,
            },
        }

        self.assertEqual(schema, expected_schema)

    def test_selectboxes(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "selectboxes",
                        "type": "selectboxes",
                        "label": "Selectboxes",
                        "values": [
                            {"label": "a", "value": "a"},
                            {"label": "b", "value": "b"},
                        ],
                        "validate": {"required": False},
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        component = form_def.configuration_wrapper["selectboxes"]
        var = form.formvariable_set.get(key="selectboxes")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "json_dump", self.options)

        expected_schema = {
            "title": "Selectboxes",
            "type": "object",
            "properties": {
                "a": {"type": "boolean"},
                "b": {"type": "boolean"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        }

        self.assertEqual(schema, expected_schema)

    def test_selectboxes_as_list(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "selectboxes_as_list",
                        "type": "selectboxes",
                        "label": "Selectboxes as list",
                        "values": [
                            {"label": "a", "value": "a"},
                            {"label": "b", "value": "b"},
                        ],
                        "validate": {"required": False},
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        options: GenericJSONOptions = {
            "service": self.service,
            "path": "",
            "variables": [],
            "fixed_metadata_variables": [],
            "additional_metadata_variables": [],
            "transform_to_list": ["selectboxes_as_list"],
        }

        component = form_def.configuration_wrapper["selectboxes_as_list"]
        var = form.formvariable_set.get(key="selectboxes_as_list")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "json_dump", options)

        expected_schema = {
            "title": "Selectboxes as list",
            "type": "array",
            "items": {"type": "string", "enum": ["a", "b"]},
        }

        self.assertEqual(schema, expected_schema)

    def test_edit_grid(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "editgrid",
                        "type": "editgrid",
                        "label": "Editgrid",
                        "components": [
                            {
                                "type": "file",
                                "key": "file",
                                "label": "file",
                                "storage": "url",
                                "url": "",
                                "useConfigFiletypes": False,
                                "filePattern": "",
                                "file": {"allowedTypesLabels": []},
                                "multiple": False,
                            },
                            {
                                "type": "file",
                                "key": "file_multiple",
                                "label": "file multiple",
                                "storage": "url",
                                "url": "",
                                "useConfigFiletypes": False,
                                "filePattern": "",
                                "file": {"allowedTypesLabels": []},
                                "multiple": True,
                            },
                            {
                                "key": "selectboxes",
                                "type": "selectboxes",
                                "label": "Selectboxes",
                                "values": [
                                    {"label": "a", "value": "a"},
                                    {"label": "b", "value": "b"},
                                ],
                                "validate": {"required": False},
                            },
                        ],
                    },
                ]
            }
        )
        FormStepFactory.create(form=form, form_definition=form_def)

        component = form_def.configuration_wrapper["editgrid"]
        var = form.formvariable_set.get(key="editgrid")
        schema = var.as_json_schema()

        process_variable_schema(component, schema, "json_dump", self.options)

        expected_schema = {
            "title": "Editgrid",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {
                        "title": "file",
                        "type": ["null", "object"],
                        "properties": {
                            "file_name": {"type": "string"},
                            "content": {"type": "string", "format": "base64"},
                        },
                        "required": ["file_name", "content"],
                        "additionalProperties": False,
                    },
                    "file_multiple": {
                        "title": "file multiple",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "file_name": {"type": "string"},
                                "content": {"type": "string", "format": "base64"},
                            },
                            "required": ["file_name", "content"],
                            "additionalProperties": False,
                        },
                    },
                    "selectboxes": {
                        "title": "Selectboxes",
                        "type": "object",
                        "properties": {
                            "a": {"type": "boolean"},
                            "b": {"type": "boolean"},
                        },
                        "required": ["a", "b"],
                        "additionalProperties": False,
                    },
                },
                "required": ["file", "file_multiple", "selectboxes"],
                "additionalProperties": False,
            },
        }

        self.assertEqual(schema, expected_schema)
