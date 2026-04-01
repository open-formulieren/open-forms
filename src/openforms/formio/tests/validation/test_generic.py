from django.test import SimpleTestCase

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class ValidateFormioDataTests(SimpleTestCase):
    def test_nested_keys_and_fields_being_required(self):
        component: Component = {
            "type": "textfield",
            "key": "nested.field",
            "label": "Nested data",
            "validate": {"required": True},
        }

        is_valid, errors = validate_formio_data(component, {})

        self.assertFalse(is_valid)
        error = extract_error(errors, "nested")
        self.assertEqual(error.code, "required")
