from django.test import SimpleTestCase

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


class ComponentValidJsonSchemaTests(SimpleTestCase):
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
        schema = as_json_schema(component)
        self.assertIsNone(schema)

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

    def test_postcode(self):
        component: Component = {
            "label": "Postcode",
            "key": "postcode",
            "type": "postcode",
        }
        self.assertComponentSchemaIsValid(component=component, multiple=True)

    def test_partners(self):
        component: Component = {
            "label": "Partners",
            "key": "partners",
            "type": "partners",
        }
        self.assertComponentSchemaIsValid(component=component)


class GeneralComponentSchemaTests(SimpleTestCase):
    def test_description(self):
        component: Component = {
            "label": "This is a label",
            "key": "textfield",
            "type": "textfield",
            "description": "This is a description",
        }

        schema = as_json_schema(component)
        self.assertEqual(schema["description"], "This is a description")


class RadioTests(SimpleTestCase):
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


class SelectTests(SimpleTestCase):
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


class SelectBoxesTests(SimpleTestCase):
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


class MapTests(SimpleTestCase):
    def test_marker(self):
        component: MapComponent = {
            "label": "Map",
            "key": "map",
            "type": "map",
            "useConfigDefaultMapSettings": False,
            "interactions": {"marker": True, "polygon": False, "polyline": False},
        }

        expected_schema = {
            "title": "Map",
            "type": "object",
            "required": ["type", "coordinates"],
            "additionalProperties": False,
            "properties": {
                "type": {"type": "string", "const": "Point"},
                "coordinates": {
                    "type": "array",
                    "prefixItems": [
                        {"title": "Longitude", "type": "number"},
                        {"title": "Latitude", "type": "number"},
                    ],
                    "items": False,
                    "minItems": 2,
                },
            },
        }

        schema = as_json_schema(component)
        self.assertEqual(schema, expected_schema)

    def test_polyline(self):
        component: MapComponent = {
            "label": "Map",
            "key": "map",
            "type": "map",
            "useConfigDefaultMapSettings": False,
            "interactions": {"marker": False, "polygon": False, "polyline": True},
        }

        expected_schema = {
            "title": "Map",
            "type": "object",
            "required": ["type", "coordinates"],
            "additionalProperties": False,
            "properties": {
                "type": {"type": "string", "const": "LineString"},
                "coordinates": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "array",
                        "prefixItems": [
                            {"title": "Longitude", "type": "number"},
                            {"title": "Latitude", "type": "number"},
                        ],
                        "items": False,
                        "minItems": 2,
                    },
                },
            },
        }

        schema = as_json_schema(component)
        self.assertEqual(schema, expected_schema)

    def test_polygon(self):
        component: MapComponent = {
            "label": "Map",
            "key": "map",
            "type": "map",
            "useConfigDefaultMapSettings": False,
            "interactions": {"marker": False, "polygon": True, "polyline": False},
        }

        expected_schema = {
            "title": "Map",
            "type": "object",
            "required": ["type", "coordinates"],
            "additionalProperties": False,
            "properties": {
                "type": {"type": "string", "const": "Polygon"},
                "coordinates": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {
                        "type": "array",
                        "minItems": 4,
                        "items": {
                            "type": "array",
                            "prefixItems": [
                                {"title": "Longitude", "type": "number"},
                                {"title": "Latitude", "type": "number"},
                            ],
                            "items": False,
                            "minItems": 2,
                        },
                    },
                },
            },
        }

        schema = as_json_schema(component)
        self.assertEqual(schema, expected_schema)

    def test_all(self):
        component: MapComponent = {
            "label": "Map",
            "key": "map",
            "type": "map",
            "useConfigDefaultMapSettings": False,
            "interactions": {"marker": True, "polygon": True, "polyline": True},
        }

        expected_schema = {
            "title": "Map",
            "type": "object",
            "required": ["type", "coordinates"],
            "oneOf": [
                {
                    "additionalProperties": False,
                    "properties": {
                        "coordinates": {
                            "items": False,
                            "minItems": 2,
                            "prefixItems": [
                                {"title": "Longitude", "type": "number"},
                                {"title": "Latitude", "type": "number"},
                            ],
                            "type": "array",
                        },
                        "type": {"const": "Point", "type": "string"},
                    },
                },
                {
                    "additionalProperties": False,
                    "properties": {
                        "coordinates": {
                            "items": {
                                "items": {
                                    "items": False,
                                    "minItems": 2,
                                    "prefixItems": [
                                        {"title": "Longitude", "type": "number"},
                                        {"title": "Latitude", "type": "number"},
                                    ],
                                    "type": "array",
                                },
                                "minItems": 4,
                                "type": "array",
                            },
                            "maxItems": 1,
                            "minItems": 1,
                            "type": "array",
                        },
                        "type": {"const": "Polygon", "type": "string"},
                    },
                },
                {
                    "additionalProperties": False,
                    "properties": {
                        "coordinates": {
                            "items": {
                                "items": False,
                                "minItems": 2,
                                "prefixItems": [
                                    {"title": "Longitude", "type": "number"},
                                    {"title": "Latitude", "type": "number"},
                                ],
                                "type": "array",
                            },
                            "minItems": 2,
                            "type": "array",
                        },
                        "type": {"const": "LineString", "type": "string"},
                    },
                },
            ],
        }

        schema = as_json_schema(component)
        self.assertEqual(schema, expected_schema)


class TextFieldTests(SimpleTestCase):
    def test_validation_rules_are_added(self):
        component: TextFieldComponent = {
            "label": "Text field",
            "key": "textfield",
            "type": "textfield",
            "validate": {"pattern": "^[A-Z]$", "maxLength": 10},
        }

        with self.subTest("single"):
            schema = as_json_schema(component)
            self.assertEqual(schema["pattern"], "^[A-Z]$")
            self.assertEqual(schema["maxLength"], 10)

        with self.subTest("multiple"):
            component["multiple"] = True
            schema = as_json_schema(component)
            self.assertEqual(schema["items"]["pattern"], "^[A-Z]$")
            self.assertEqual(schema["items"]["maxLength"], 10)


class TextAreaTests(SimpleTestCase):
    def test_validation_rules_are_added(self):
        component: TextFieldComponent = {
            "label": "Text area",
            "key": "textarea",
            "type": "textarea",
            "validate": {"pattern": "^[A-Z]$", "maxLength": 10},
        }

        with self.subTest("single"):
            schema = as_json_schema(component)
            self.assertEqual(schema["pattern"], "^[A-Z]$")
            self.assertEqual(schema["maxLength"], 10)

        with self.subTest("multiple"):
            component["multiple"] = True
            schema = as_json_schema(component)
            self.assertEqual(schema["items"]["pattern"], "^[A-Z]$")
            self.assertEqual(schema["items"]["maxLength"], 10)


class PostcodeTests(SimpleTestCase):
    def test_includes_pattern_by_default(self):
        component: Component = {
            "label": "Postcode",
            "key": "postcode",
            "type": "postcode",
        }

        with self.subTest("single"):
            schema = as_json_schema(component)
            self.assertIn("pattern", schema)

        with self.subTest("multiple"):
            component["multiple"] = True
            schema = as_json_schema(component)
            self.assertIn("pattern", schema["items"])

    def test_includes_custom_pattern(self):
        component: Component = {
            "label": "Postcode",
            "key": "postcode",
            "type": "postcode",
            "validate": {"pattern": r"\d{4} [A-Z]{2}"},
        }

        with self.subTest("single"):
            schema = as_json_schema(component)
            self.assertEqual(schema["pattern"], r"\d{4} [A-Z]{2}")

        with self.subTest("multiple"):
            component["multiple"] = True
            schema = as_json_schema(component)
            self.assertEqual(schema["items"]["pattern"], r"\d{4} [A-Z]{2}")


class PhoneNumberTests(SimpleTestCase):
    def test_includes_pattern_by_default(self):
        component: Component = {
            "label": "Phone number",
            "key": "phonenumber",
            "type": "phoneNumber",
        }

        with self.subTest("single"):
            schema = as_json_schema(component)
            self.assertIn("pattern", schema)

        with self.subTest("multiple"):
            component["multiple"] = True
            schema = as_json_schema(component)
            self.assertIn("pattern", schema["items"])

    def test_includes_custom_pattern(self):
        component: Component = {
            "label": "Phone number",
            "key": "phonenumber",
            "type": "phoneNumber",
            "validate": {"pattern": r"\d{10}"},
        }

        with self.subTest("single"):
            schema = as_json_schema(component)
            self.assertEqual(schema["pattern"], r"\d{10}")

        with self.subTest("multiple"):
            component["multiple"] = True
            schema = as_json_schema(component)
            self.assertEqual(schema["items"]["pattern"], r"\d{10}")


class NumberTests(SimpleTestCase):
    def test_includes_minimum_maximum_values(self):
        component: Component = {
            "label": "Number",
            "key": "number",
            "type": "number",
            "validate": {"min": 10, "max": 20},
        }

        with self.subTest("single"):
            schema = as_json_schema(component)
            self.assertEqual(schema["minimum"], 10)
            self.assertEqual(schema["maximum"], 20)

        with self.subTest("multiple"):
            component["multiple"] = True
            schema = as_json_schema(component)
            self.assertEqual(schema["items"]["minimum"], 10)
            self.assertEqual(schema["items"]["maximum"], 20)


class CurrencyTests(SimpleTestCase):
    def test_includes_minimum_maximum_values(self):
        component: Component = {
            "label": "Currency",
            "key": "currency",
            "type": "currency",
            "validate": {"min": 10, "max": 20},
        }

        schema = as_json_schema(component)
        self.assertEqual(schema["minimum"], 10)
        self.assertEqual(schema["maximum"], 20)


class EditGridTests(SimpleTestCase):
    maxDiff = None

    def test_generate_schema(self):
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
                    "key": "emailAddress",
                    "label": "Email address",
                    "type": "email",
                },
            ],
        }

        schema = as_json_schema(component)

        expected_schema = {
            "title": "Repeating Group Outer",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "repeatingGroupInner": {
                        "title": "Repeating Group Inner",
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "textFieldInner": {
                                    "type": "string",
                                    "title": "Text field",
                                },
                            },
                            "required": ["textFieldInner"],
                            "additionalProperties": False,
                        },
                    },
                    "emailAddress": {
                        "type": "string",
                        "format": "email",
                        "title": "Email address",
                    },
                },
                "required": ["repeatingGroupInner", "emailAddress"],
                "additionalProperties": False,
            },
        }
        self.assertEqual(schema, expected_schema)

    def test_includes_maximum_length(self):
        component: EditGridComponent = {
            "key": "repeatingGroup",
            "label": "Repeating Group",
            "type": "editgrid",
            "components": [
                {
                    "key": "textField",
                    "label": "Text field",
                    "type": "textfield",
                }
            ],
            "validate": {"maxLength": 10},
        }

        schema = as_json_schema(component)
        self.assertEqual(schema["maxItems"], 10)

    def test_textfield_inside_fieldset_inside_editgrid(self):
        component: EditGridComponent = {
            "key": "editgrid",
            "label": "editgrid",
            "type": "editgrid",
            "components": [
                {
                    "key": "fieldset",
                    "label": "fieldset",
                    "type": "fieldset",
                    "components": [
                        {
                            "key": "textfield",
                            "label": "Text field",
                            "type": "textfield",
                        },
                    ],
                },
            ],
        }

        schema = as_json_schema(component)

        expected_schema = {
            "title": "editgrid",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"textfield": {"title": "Text field", "type": "string"}},
                "required": ["textfield"],
                "additionalProperties": False,
            },
        }
        self.assertEqual(schema, expected_schema)

    def test_textfields_inside_columns_inside_editgrid(self):
        component: EditGridComponent = {
            "key": "editgrid",
            "label": "editgrid",
            "type": "editgrid",
            "components": [
                {
                    "type": "columns",
                    "key": "columns",
                    "label": "Columns",
                    "columns": [
                        {
                            "size": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "textfield1",
                                    "label": "textfield1",
                                }
                            ],
                        },
                        {
                            "size": 6,
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "textfield2",
                                    "label": "textfield2",
                                }
                            ],
                        },
                    ],
                },
            ],
        }

        schema = as_json_schema(component)

        expected_schema = {
            "title": "editgrid",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "textfield1": {"title": "textfield1", "type": "string"},
                    "textfield2": {"title": "textfield2", "type": "string"},
                },
                "required": ["textfield1", "textfield2"],
                "additionalProperties": False,
            },
        }
        self.assertEqual(schema, expected_schema)

    def test_textfield_and_content_inside_editgrid(self):
        component: EditGridComponent = {
            "key": "editgrid",
            "label": "editgrid",
            "type": "editgrid",
            "components": [
                {
                    "type": "content",
                    "key": "content",
                    "label": "Content",
                    "html": "<p>Some content</p>",
                },
                {
                    "type": "textfield",
                    "key": "textfield",
                    "label": "Text field",
                },
            ],
        }

        schema = as_json_schema(component)

        expected_schema = {
            "title": "editgrid",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"textfield": {"title": "Text field", "type": "string"}},
                "required": ["textfield"],
                "additionalProperties": False,
            },
        }
        self.assertEqual(schema, expected_schema)

    def test_content_inside_fieldset_inside_editgrid(self):
        component: EditGridComponent = {
            "key": "editgrid",
            "label": "editgrid",
            "type": "editgrid",
            "components": [
                {
                    "type": "fieldset",
                    "key": "fieldset",
                    "label": "Fieldset",
                    "components": [
                        {
                            "type": "content",
                            "key": "content",
                            "label": "Content",
                            "html": "<p>Some content</p>",
                        },
                        {
                            "type": "textfield",
                            "key": "textfield",
                            "label": "Text field",
                        },
                    ],
                },
            ],
        }

        schema = as_json_schema(component)

        expected_schema = {
            "title": "editgrid",
            "type": "array",
            "items": {
                "properties": {"textfield": {"title": "Text field", "type": "string"}},
                "required": ["textfield"],
                "type": "object",
                "additionalProperties": False,
            },
        }
        self.assertEqual(schema, expected_schema)

    def test_textfield_inside_fieldset_inside_fieldset_inside_editgrid(self):
        component: EditGridComponent = {
            "key": "editgrid",
            "label": "editgrid",
            "type": "editgrid",
            "components": [
                {
                    "type": "fieldset",
                    "key": "fieldset1",
                    "label": "Fieldset1",
                    "components": [
                        {
                            "type": "fieldset",
                            "key": "fieldset2",
                            "label": "Fieldset2",
                            "components": [
                                {
                                    "type": "textfield",
                                    "key": "textfield",
                                    "label": "Text field",
                                }
                            ],
                        },
                    ],
                },
            ],
        }

        schema = as_json_schema(component)

        expected_schema = {
            "title": "editgrid",
            "type": "array",
            "items": {
                "properties": {"textfield": {"title": "Text field", "type": "string"}},
                "required": ["textfield"],
                "type": "object",
                "additionalProperties": False,
            },
        }
        self.assertEqual(schema, expected_schema)


class AddressNLTests(SimpleTestCase):
    def test_includes_pattern_by_default(self):
        component: AddressNLComponent = {
            "label": "Address NL",
            "key": "addressNL",
            "type": "addressNL",
            "deriveAddress": False,
        }

        schema = as_json_schema(component)
        for field in ("houseLetter", "houseNumber", "houseNumberAddition", "postcode"):
            self.assertIn("pattern", schema["properties"][field])

    def test_includes_custom_patterns(self):
        component: AddressNLComponent = {
            "label": "Address NL",
            "key": "addressNL",
            "type": "addressNL",
            "deriveAddress": False,
            "openForms": {
                "components": {
                    "postcode": {
                        "validate": {
                            "pattern": r"^1234 [A-Z]{2}$",
                        },
                        "translatedErrors": {},
                    },
                    "city": {
                        "validate": {"pattern": r"Amsterdam"},
                        "translatedErrors": {},
                    },
                }
            },
        }

        schema = as_json_schema(component)

        self.assertEqual(
            schema["properties"]["postcode"]["pattern"], r"^1234 [A-Z]{2}$"
        )
        self.assertEqual(schema["properties"]["city"]["pattern"], r"Amsterdam")
