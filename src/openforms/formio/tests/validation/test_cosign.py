from django.test import SimpleTestCase


from openforms.typing import JSONValue


from ...typing import Component
from .helpers import extract_error, validate_formio_data


class CosignValidationTests(SimpleTestCase):
    def test_cosign_required_validation(self):
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

    def test_cosign_pattern_validation(self):
        component: Component = {
            "type": "cosign",
            "key": "foo",
            "label": "Test",
        }
        data: JSONValue = {"foo": "invalid-email"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")
