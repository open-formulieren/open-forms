from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class PhoneNumberValidationTests(SimpleTestCase):
    def test_phonenumber_required_validation(self):
        component: Component = {
            "type": "phoneNumber",
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

    def test_pattern_validation(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "foo",
            "label": "Test",
            "validate": {
                "required": True,
                "pattern": r"06[ -]?[\d ]+",  # only allow mobile numbers
            },
        }
        data: JSONValue = {"foo": "020-123 456"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")

    def test_phonenumber_maxlength(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "foo",
            "label": "Test",
            "validate": {
                "required": True,
                "maxLength": 8,
            },
        }
        data: JSONValue = {"foo": "020123456"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "max_length")