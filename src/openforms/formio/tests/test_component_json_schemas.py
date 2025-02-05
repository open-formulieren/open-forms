from django.test import TestCase

from jsonschema import Draft202012Validator

from openforms.formio.constants import DataSrcOptions

from ..service import as_json_schema
from ..typing import (
    AddressNLComponent,
    Component,
    ContentComponent,
    DateComponent,
    DatetimeComponent,
    EditGridComponent,
    FileComponent,
    MapComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
    TextFieldComponent,
)


class ComponentValidJsonSchemaTests(TestCase):
    validator = Draft202012Validator

    def assertValidSchema(self, properties):
        schema = {
            "$schema": self.validator.META_SCHEMA["$id"],
            **properties,
        }

        self.assertIn("type", schema)
        self.validator.check_schema(schema)

    def assertComponentSchemaIsValid(self, *, component, multiple=False):
        with self.subTest():
            schema = as_json_schema(component)

            self.assertValidSchema(schema)

        if multiple:
            with self.subTest(multiple=multiple):
                component["multiple"] = True
                schema = as_json_schema(component)

                self.assertValidSchema(schema)

    def test_checkbox(self):
        component: Component = {
            "label": "Checkbox",
            "key": "checkbox",
            "type": "checkbox",
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_content(self):
        component: ContentComponent = {
            "label": "Content",
            "key": "content",
            "html": "ASDF",
            "type": "content",
        }
        with self.assertRaises(NotImplementedError):
            as_json_schema(component)

    def test_currency(self):
        component: Component = {
            "label": "Currency",
            "key": "currency",
            "type": "currency",
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_edit_grid(self):
        component: EditGridComponent = {
            "key": "repeatingGroup",
            "label": "Repeating Group Outer",
            "type": "editgrid",
            "components": [
                {
                    "key": "repeatingGroupInner",
                    "label": "Repeating Group Inner",
                    "type": "editgrid",
                    "components": [
                        {
                            "key": "textFieldInner",
                            "label": "Text field",
                            "type": "textfield",
                        },
                    ],
                },
                {
                    "key": "eMailadres",
                    "label": "Email address",
                    "type": "email",
                },
            ],
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_email(self):
        component: Component = {"label": "Email field", "key": "email", "type": "email"}
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_file(self):
        component: FileComponent = {
            "label": "File",
            "key": "file",
            "type": "file",
            "storage": "url",
            "url": "https://example.com",
            "useConfigFiletypes": False,
            "filePattern": "",
            "file": {"allowedTypesLabels": []},
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_number(self):
        component: Component = {"label": "Number", "key": "number", "type": "number"}
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_phone_number(self):
        component: Component = {
            "label": "Phone number",
            "key": "phone",
            "type": "phoneNumber",
        }
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_radio(self):
        component: RadioComponent = {
            "label": "Radio",
            "key": "radio",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
            "type": "radio",
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_select(self):
        component: SelectComponent = {
            "label": "Select",
            "key": "select",
            "data": {
                "values": [
                    {"label": "A", "value": "a"},
                    {"label": "B", "value": "b"},
                ],
            },
            "type": "select",
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_select_boxes(self):
        component: SelectBoxesComponent = {
            "label": "Select boxes",
            "key": "selectBoxes",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
            "type": "selectboxes",
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_signature(self):
        component: Component = {
            "label": "Signature",
            "key": "signature",
            "type": "signature",
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_text_area(self):
        component: Component = {
            "label": "TextArea",
            "key": "textArea",
            "type": "textarea",
        }
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_text_field(self):
        component: TextFieldComponent = {
            "label": "Text field",
            "key": "text",
            "type": "textfield",
        }
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_time(self):
        component: Component = {"label": "Time", "key": "time", "type": "time"}
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_bsn(self):
        component: Component = {"label": "BSN", "key": "bsn", "type": "bsn"}
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_address_nl(self):
        component: AddressNLComponent = {
            "label": "Address NL",
            "key": "addressNL",
            "type": "addressNL",
            "deriveAddress": False,
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_cosign(self):
        component: Component = {"label": "Cosign", "key": "cosign", "type": "cosign"}
        self.assertComponentSchemaIsValid(component=component)

    def test_date(self):
        component: DateComponent = {"label": "Date", "key": "date", "type": "date"}
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_date_time(self):
        component: DatetimeComponent = {
            "label": "DateTime",
            "key": "datetime",
            "type": "datetime",
        }
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_iban(self):
        component: Component = {"label": "Iban", "key": "iban", "type": "iban"}
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_license_plate(self):
        component: Component = {
            "label": "License Plate",
            "key": "licenseplate",
            "type": "licenseplate",
        }
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_map(self):
        component: MapComponent = {
            "label": "Map",
            "key": "map",
            "type": "map",
            "useConfigDefaultMapSettings": False,
        }
        self.assertComponentSchemaIsValid(component=component)

    def test_postcode(self):
        component: Component = {
            "label": "Postcode",
            "key": "postcode",
            "type": "postcode",
        }
        self.assertComponentSchemaIsValid(component=component, multiple=True)


class RadioTests(TestCase):

    def test_manual_data_source(self):
        component: RadioComponent = {
            "label": "Radio label",
            "key": "radio",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
            "type": "radio",
        }

        expected_schema = {
            "title": "Radio label",
            "type": "string",
            "enum": ["a", "b", ""],
        }
        schema = as_json_schema(component)
        self.assertEqual(expected_schema, schema)

    def test_data_source_is_another_form_variable(self):
        component: RadioComponent = {
            "label": "Radio label",
            "key": "radio",
            "values": [
                {"label": "", "value": ""},
            ],
            "openForms": {"dataSrc": DataSrcOptions.variable},
            "type": "radio",
        }

        expected_schema = {"title": "Radio label", "type": "string"}
        schema = as_json_schema(component)
        self.assertEqual(expected_schema, schema)


class SelectTests(TestCase):

    def test_manual_data_source(self):
        component: SelectComponent = {
            "label": "Select label",
            "key": "select",
            "data": {
                "values": [
                    {"label": "A", "value": "a"},
                    {"label": "B", "value": "b"},
                ],
            },
            "type": "select",
        }

        with self.subTest("single"):
            expected_schema = {
                "title": "Select label",
                "type": "string",
                "enum": ["a", "b", ""],
            }
            schema = as_json_schema(component)
            self.assertEqual(schema, expected_schema)

        with self.subTest("multiple"):
            component["multiple"] = True
            expected_schema = {
                "title": "Select label",
                "type": "array",
                "items": {"type": "string", "enum": ["a", "b", ""]},
            }
            schema = as_json_schema(component)
            self.assertEqual(schema, expected_schema)

    def test_data_source_is_another_form_variable(self):
        component: SelectComponent = {
            "label": "Select label",
            "key": "select",
            "data": {
                "values": [
                    {"label": "", "value": ""},
                ],
            },
            "openForms": {"dataSrc": DataSrcOptions.variable},
            "type": "select",
        }

        with self.subTest("single"):
            expected_schema = {"title": "Select label", "type": "string"}
            schema = as_json_schema(component)
            self.assertEqual(schema, expected_schema)

        with self.subTest("multiple"):
            component["multiple"] = True
            expected_schema = {
                "title": "Select label",
                "type": "array",
                "items": {"type": "string"},
            }
            schema = as_json_schema(component)
            self.assertEqual(schema, expected_schema)


class SelectBoxesTests(TestCase):
    def test_manual_data_source(self):
        component: SelectBoxesComponent = {
            "label": "Select boxes label",
            "key": "selectBoxes",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
            "type": "selectboxes",
        }

        expected_schema = {
            "title": "Select boxes label",
            "type": "object",
            "properties": {
                "a": {"type": "boolean"},
                "b": {"type": "boolean"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        }
        schema = as_json_schema(component)
        self.assertEqual(schema, expected_schema)

    def test_data_source_is_another_form_variable(self):
        component: SelectBoxesComponent = {
            "label": "Select boxes label",
            "key": "selectBoxes",
            "values": [
                {"label": "", "value": ""},
            ],
            "openForms": {"dataSrc": DataSrcOptions.variable},
            "type": "selectboxes",
        }

        expected_schema = {
            "title": "Select boxes label",
            "type": "object",
            "additionalProperties": True,
        }
        schema = as_json_schema(component)
        self.assertEqual(schema, expected_schema)
