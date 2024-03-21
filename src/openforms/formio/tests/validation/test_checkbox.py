from django.test import SimpleTestCase

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class CheckboxValidationTests(SimpleTestCase):

    def test_checkbox_field_required_validation(self):
        component: Component = {
            "type": "checkbox",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": ""}, "invalid"),
            ({"foo": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)
