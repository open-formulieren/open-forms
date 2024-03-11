from django.test import SimpleTestCase, tag

from openforms.typing import JSONValue

from ...typing import TextFieldComponent
from .helpers import extract_error, validate_formio_data


class TextFieldValidationTests(SimpleTestCase):
    def test_textfield_required_validation(self):
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": ""}, "blank"),
            ({"foo": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_textfield_max_length(self):
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "foo",
            "label": "Test",
            "validate": {"maxLength": 3},
        }

        is_valid, errors = validate_formio_data(component, {"foo": "barbaz"})

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "max_length")

    @tag("gh-3977")
    def test_textfield_regex_housenumber(self):
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "houseNumber",
            "label": "House number",
            "validate": {"pattern": r"[0-9]{1,5}"},
        }
        data: JSONValue = {"houseNumber": "<div>injection</div>"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "houseNumber")
        self.assertEqual(error.code, "invalid")
