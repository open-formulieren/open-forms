from django.test import TestCase

from jsonschema import Draft202012Validator

from openforms.formio.components.custom import (
    BSN,
    AddressNL,
    Cosign,
    Date,
    Datetime,
    Iban,
    LicensePlate,
    Map,
    Postcode,
)
from openforms.formio.components.vanilla import (
    Checkbox,
    Content,
    Currency,
    EditGrid,
    Email,
    File,
    Number,
    PhoneNumber,
    Radio,
    Select,
    SelectBoxes,
    Signature,
    TextArea,
    TextField,
    Time,
)


# TODO-4980: add typing and include all values for the component dicts
class CustomComponentValidJsonSchemaTests(TestCase):

    validator = Draft202012Validator

    def check_schema(self, properties):
        schema = {
            "$schema": self.validator.META_SCHEMA["$id"],
            **properties,
        }

        self.validator.check_schema(schema)

    # TODO-4980: currently all components are testing for `multiple=True` which is not
    #  useful for all
    def _test_component(self, component_class, component):
        with self.subTest(f"single {component["label"]}"):
            schema = component_class.as_json_schema(component)

            print(schema)
            self.check_schema(schema)

        with self.subTest(f"multiple {component["label"]}"):
            component["multiple"] = True
            schema = component_class.as_json_schema(component)

            self.check_schema(schema)

    def test_checkbox(self):
        component_class = Checkbox
        component = {"label": "Checkbox", "key": "checkbox"}
        self._test_component(component_class, component)

    def test_content(self):
        component_class = Content
        component = {
            "label": "Content", "key": "content", "html": "ASDF", "type": "content"
        }
        with self.assertRaises(NotImplementedError):
            component_class.as_json_schema(component)

    def test_currency(self):
        component_class = Currency
        component = {"label": "Currency", "key": "currency"}
        self._test_component(component_class, component)

    def test_edit_grid(self):
        component_class = EditGrid
        component = {
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
        self._test_component(component_class, component)

    def test_email(self):
        component_class = Email
        component = {"label": "Email field", "key": "email"}
        self._test_component(component_class, component)

    def test_file(self):
        component_class = File
        component = {"label": "File", "key": "file"}
        self._test_component(component_class, component)

    def test_number(self):
        component_class = Number
        component = {"label": "Number", "key": "number"}
        self._test_component(component_class, component)

    def test_phone_number(self):
        component_class = PhoneNumber
        component = {"label": "Phone number", "key": "phone"}
        self._test_component(component_class, component)

    def test_radio(self):
        component_class = Radio
        component = {
            "label": "Radio",
            "key": "radio",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
        }
        self._test_component(component_class, component)

    def test_select(self):
        component_class = Select
        component = {
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
        self._test_component(component_class, component)

    def test_select_boxes(self):
        component_class = SelectBoxes
        component = {
            "label": "Select boxes",
            "key": "selectBoxes",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ]
        }
        self._test_component(component_class, component)

    def test_signature(self):
        component_class = Signature
        component = {"label": "Signature", "key": "signature"}
        self._test_component(component_class, component)

    def test_text_area(self):
        component_class = TextArea
        component = {"label": "TextArea", "key": "textArea"}
        self._test_component(component_class, component)

    def test_text_field(self):
        component_class = TextField
        component = {"label": "Text field", "key": "text"}
        self._test_component(component_class, component)

    def test_time(self):
        component_class = Time
        component = {"label": "Time", "key": "time"}
        self._test_component(component_class, component)


class VanillaComponentValidJsonSchemaTests(TestCase):
    validator = Draft202012Validator

    def check_schema(self, properties):
        schema = {
            "$schema": self.validator.META_SCHEMA["$id"],
            **properties,
        }

        self.validator.check_schema(schema)

    # TODO-4980: currently all components are testing for `multiple=True` which is not
    #  useful for all
    def _test_component(self, component_class, component):
        with self.subTest(f"single {component["label"]}"):
            schema = component_class.as_json_schema(component)

            print(schema)
            self.check_schema(schema)

        with self.subTest(f"multiple {component["label"]}"):
            component["multiple"] = True
            schema = component_class.as_json_schema(component)

            self.check_schema(schema)

    def test_bsn(self):
        component_class =  BSN
        component = {"label": "BSN", "key": "bsn"}
        self._test_component(component_class, component)

    def test_address_nl(self):
        component_class =  AddressNL
        component = {"label": "Address NL", "key": "addressNL"}
        self._test_component(component_class, component)

    def test_cosign(self):
        component_class =  Cosign
        component = {"label": "Cosign", "key": "cosign"}
        self._test_component(component_class, component)

    def test_date(self):
        component_class =  Date
        component = {"label": "Date", "key": "date"}
        self._test_component(component_class, component)

    def test_date_time(self):
        component_class =  Datetime
        component = {"label": "DateTime", "key": "datetime"}
        self._test_component(component_class, component)

    def test_iban(self):
        component_class =  Iban
        component = {"label": "Iban", "key": "iban"}
        self._test_component(component_class, component)

    def test_license_plate(self):
        component_class =  LicensePlate
        component = {"label": "License Plate", "key": "licenseplate"}
        self._test_component(component_class, component)

    def test_map(self):
        component_class =  Map
        component = {"label": "Map", "key": "map"}
        self._test_component(component_class, component)

    def test_postcode(self):
        component_class =  Postcode
        component = {"label": "Postcode", "key": "postcode"}
        self._test_component(component_class, component)


class RadioTests(TestCase):

    def test_manual_data_source(self):
        component = {
            "label": "Radio label",
            "key": "radio",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
        }

        expected_schema = {
            "title": "Radio label",
            "type": "string",
            "enum": ["a", "b", ""],
        }
        schema = Radio.as_json_schema(component)
        self.assertEqual(expected_schema, schema)

    def test_data_source_is_another_form_variable(self):
        component = {
            "label": "Radio label",
            "key": "radio",
            "values": [
                {"label": "", "value": ""},
            ],
            "openForms": {"dataSrc": "variable"},
        }

        expected_schema = {"title": "Radio label", "type": "string"}
        schema = Radio.as_json_schema(component)
        self.assertEqual(expected_schema, schema)



class SelectTests(TestCase):

    def test_manual_data_source(self):
        component = {
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
                "title": "Select label", "type": "string", "enum": ["a", "b", ""]
            }
            schema = Select.as_json_schema(component)
            self.assertEqual(schema, expected_schema)

        with self.subTest("multiple"):
            component["multiple"] = True
            expected_schema = {
                "title": "Select label",
                "type": "array",
                "items": {"type": "string", "enum": ["a", "b", ""]},
            }
            schema = Select.as_json_schema(component)
            self.assertEqual(schema, expected_schema)

    def test_data_source_is_another_form_variable(self):
        component = {
            "label": "Select label",
            "key": "select",
            "data": {
                "values": [
                    {"label": "", "value": ""},
                ],
            },
            "openForms": {"dataSrc": "variable"},
            "type": "select",
        }

        with self.subTest("single"):
            expected_schema = {"title": "Select label", "type": "string"}
            schema = Select.as_json_schema(component)
            self.assertEqual(schema, expected_schema)

        with self.subTest("multiple"):
            component["multiple"] = True
            expected_schema = {
                "title": "Select label", "type": "array", "items": {"type": "string"}
            }
            schema = Select.as_json_schema(component)
            self.assertEqual(schema, expected_schema)


class SelectBoxesTests(TestCase):
    def test_manual_data_source(self):
        component = {
            "label": "Select boxes label",
            "key": "selectBoxes",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ]
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
        schema = SelectBoxes.as_json_schema(component)
        self.assertEqual(schema, expected_schema)

    def test_data_source_is_another_form_variable(self):
        component = {
            "label": "Select boxes label",
            "key": "selectBoxes",
            "values": [
                {"label": "", "value": ""},
            ],
            "openForms": {"dataSrc": "variable"},
        }

        expected_schema = {
            "title": "Select boxes label", "type": "object", "additionalProperties": True
        }
        schema = SelectBoxes.as_json_schema(component)
        self.assertEqual(schema, expected_schema)
