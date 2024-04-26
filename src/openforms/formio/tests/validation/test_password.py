from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class PasswordFieldValidationTests(SimpleTestCase):
    def test_valid_required_passwordfield(self):
        component: Component = {
            "type": "password",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": True},
        }

        data: JSONValue = {"foo": "test"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertTrue(is_valid)
        self.assertDictEqual(errors, {})

    def test_invalid_required_passwordfield(self):
        component: Component = {
            "type": "password",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_multiple_enabled(self):
        component: Component = {
            "type": "password",
            "key": "foo",
            "label": "Foo",
            "multiple": True,
        }

        data: JSONValue = {"foo": ["ghwgG22", "TRshhe33j"]}

        is_valid, errors = validate_formio_data(component, data)

        self.assertTrue(is_valid)
        self.assertDictEqual(errors, {})

    def test_multiple_disabled(self):
        component: Component = {
            "type": "password",
            "key": "foo",
            "label": "Foo",
            "multiple": False,
        }

        data: JSONValue = {"foo": ["ghwgG22", "TRshhe33j"]}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")
