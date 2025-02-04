from django.test import SimpleTestCase, tag

from openforms.formio.constants import DataSrcOptions
from openforms.typing import JSONObject

from ...typing import RadioComponent
from .helpers import extract_error, validate_formio_data


class RadioValidationTests(SimpleTestCase):

    def test_radio_required_validation(self):
        component: RadioComponent = {
            "type": "radio",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
            "openForms": {"dataSrc": DataSrcOptions.manual},
            "values": [
                {"value": "a", "label": "A"},
                {"value": "b", "label": "B"},
            ],
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": ""}, "invalid_choice"),
            ({"foo": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_invalid_option_provided(self):
        component: RadioComponent = {
            "type": "radio",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
            "openForms": {"dataSrc": DataSrcOptions.manual},
            "values": [
                {"value": "a", "label": "A"},
                {"value": "b", "label": "B"},
            ],
        }

        with self.subTest("valid option"):
            is_valid, _ = validate_formio_data(component, {"foo": "b"})

            self.assertTrue(is_valid)

        with self.subTest("invalid option"):
            is_valid, _ = validate_formio_data(component, {"foo": "c"})

            self.assertFalse(is_valid)

    @tag("gh-4096")
    def test_radio_hidden_required(self):
        component: RadioComponent = {
            "type": "radio",
            "key": "radio",
            "label": "Radio",
            "values": [
                {"label": "Opt1", "value": "opt1"},
                {"label": "Opt2", "value": "opt2"},
            ],
            "hidden": True,
            "validate": {
                "required": True,
            },
        }

        # This happens when `clearOnHide` is `False`:
        data: JSONObject = {"radio": ""}

        is_valid, _ = validate_formio_data(component, data)
        self.assertTrue(is_valid)
