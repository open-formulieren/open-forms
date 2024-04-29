from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class CosignValidationTests(SimpleTestCase):
    def test_valid_required_cosign(self):
        component: Component = {
            "type": "cosign",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        data: JSONValue = {"foo": "user@example.com"}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_invalid_required_cosign(self):
        component: Component = {
            "type": "cosign",
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

    def test_valid_non_required_cosign(self):
        component: Component = {
            "type": "cosign",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
        }

        data: JSONValue = {"foo": "user@example.com"}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_invalid_non_required_cosign(self):
        component: Component = {
            "type": "cosign",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
        }

        data: JSONValue = {"foo": "invalid-email"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")
