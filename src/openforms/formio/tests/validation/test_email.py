from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class EmailValidationTests(SimpleTestCase):
    def test_email_required_validation(self):
        component: Component = {
            "type": "email",
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

    def test_email_pattern_validation(self):
        component: Component = {
            "type": "email",
            "key": "foo",
            "label": "Test",
        }
        data: JSONValue = {"foo": "invalid-email"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")

    def test_maxlength(self):
        component: Component = {
            "type": "email",
            "key": "foo",
            "label": "Test",
            "validate": {"maxLength": 10},
        }
        data: JSONValue = {"foo": "foobar@example.com"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "foo")
        self.assertEqual(error.code, "max_length")
