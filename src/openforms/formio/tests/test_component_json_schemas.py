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
from openforms.formio.typing import (
    AddressNLComponent,
    Component,
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


class ComponentValidJsonSchemaTestsMixin(TestCase):
    validator = Draft202012Validator

    def check_schema(self, properties):
        schema = {
            "$schema": self.validator.META_SCHEMA["$id"],
            **properties,
        }

        self.validator.check_schema(schema)

    def _test_component(self, component_class, component, multiple=False):
        with self.subTest(f"single {component['label']}"):
            schema = component_class.as_json_schema(component)

            self.check_schema(schema)

        if multiple:
            with self.subTest(f"multiple {component['label']}"):
                component["multiple"] = True
                schema = component_class.as_json_schema(component)

                self.check_schema(schema)

    def test_checkbox(self):
        component_class = Checkbox
        component: Component = {
            "label": "Checkbox",
            "key": "checkbox",
            "type": "checkbox",
        }
        self._test_component(component_class, component)

    def test_content(self):
        component_class = Content
        component = {
            "label": "Content",
            "key": "content",
            "html": "ASDF",
            "type": "content",
        }
        with self.assertRaises(NotImplementedError):
            component_class.as_json_schema(component)

    def test_currency(self):
        component_class = Currency
        component: Component = {
            "label": "Currency",
            "key": "currency",
            "type": "currency",
        }
        self._test_component(component_class, component)

    def test_edit_grid(self):
        component_class = EditGrid
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
        self._test_component(component_class, component)

    def test_email(self):
        component_class = Email
        component: Component = {"label": "Email field", "key": "email", "type": "email"}
        self._test_component(component_class, component, multiple=True)

    def test_file(self):
        component_class = File
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
        self._test_component(component_class, component)

    def test_number(self):
        component_class = Number
        component: Component = {"label": "Number", "key": "number", "type": "number"}
        self._test_component(component_class, component, multiple=True)

    def test_phone_number(self):
        component_class = PhoneNumber
        component: Component = {
            "label": "Phone number",
            "key": "phone",
            "type": "phone",
        }
        self._test_component(component_class, component, multiple=True)

    def test_radio(self):
        component_class = Radio
        component: RadioComponent = {
            "label": "Radio",
            "key": "radio",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
            "type": "radio",
        }
        self._test_component(component_class, component)

    def test_select(self):
        component_class = Select
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
        self._test_component(component_class, component)

    def test_select_boxes(self):
        component_class = SelectBoxes
        component: SelectBoxesComponent = {
            "label": "Select boxes",
            "key": "selectBoxes",
            "values": [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
            "type": "selectboxes",
        }
        self._test_component(component_class, component)

    def test_signature(self):
        component_class = Signature
        component: Component = {
            "label": "Signature",
            "key": "signature",
            "type": "signature",
        }
        self._test_component(component_class, component)

    def test_text_area(self):
        component_class = TextArea
        component: Component = {
            "label": "TextArea",
            "key": "textArea",
            "type": "textarea",
        }
        self._test_component(component_class, component, multiple=True)

    def test_text_field(self):
        component_class = TextField
        component: TextFieldComponent = {
            "label": "Text field",
            "key": "text",
            "type": "textfield",
        }
        self._test_component(component_class, component, multiple=True)

    def test_time(self):
        component_class = Time
        component: Component = {"label": "Time", "key": "time", "type": "time"}
        self._test_component(component_class, component, multiple=True)

    def test_bsn(self):
        component_class = BSN
        component: Component = {"label": "BSN", "key": "bsn", "type": "bsn"}
        self._test_component(component_class, component, multiple=True)

    def test_address_nl(self):
        component_class = AddressNL
        component: AddressNLComponent = {
            "label": "Address NL",
            "key": "addressNL",
            "type": "addressNL",
            "deriveAddress": False,
        }
        self._test_component(component_class, component)

    def test_cosign(self):
        component_class = Cosign
        component: Component = {"label": "Cosign", "key": "cosign", "type": "cosign"}
        self._test_component(component_class, component)

    def test_date(self):
        component_class = Date
        component: DateComponent = {"label": "Date", "key": "date", "type": "date"}
        self._test_component(component_class, component, multiple=True)

    def test_date_time(self):
        component_class = Datetime
        component: DatetimeComponent = {
            "label": "DateTime",
            "key": "datetime",
            "type": "datetime",
        }
        self._test_component(component_class, component, multiple=True)

    def test_iban(self):
        component_class = Iban
        component: Component = {"label": "Iban", "key": "iban", "type": "iban"}
        self._test_component(component_class, component, multiple=True)

    def test_license_plate(self):
        component_class = LicensePlate
        component: Component = {
            "label": "License Plate",
            "key": "licenseplate",
            "type": "licenseplate",
        }
        self._test_component(component_class, component, multiple=True)

    def test_map(self):
        component_class = Map
        component: MapComponent = {
            "label": "Map",
            "key": "map",
            "type": "map",
            "useConfigDefaultMapSettings": False,
        }
        self._test_component(component_class, component)

    def test_postcode(self):
        component_class = Postcode
        component: Component = {
            "label": "Postcode",
            "key": "postcode",
            "type": "postcode",
        }
        self._test_component(component_class, component, multiple=True)


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
