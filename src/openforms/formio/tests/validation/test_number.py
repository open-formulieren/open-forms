from django.test import SimpleTestCase

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class NumberValidationTests(SimpleTestCase):
    def test_number_min_value(self):
        component: Component = {
            "type": "number",
            "key": "foo",
            "label": "Test",
            "validate": {
                "min": -3.5,
            },
        }

        is_valid, errors = validate_formio_data(component, {"foo": -5.2})

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "min_value")

    def test_number_min_value_with_non_required_value(self):
        component: Component = {
            "type": "number",
            "key": "foo",
            "label": "Test",
            "validate": {"max": 10},
        }

        is_valid, _ = validate_formio_data(component, {})

        self.assertTrue(is_valid)

    def test_zero_is_accepted(self):
        component: Component = {
            "type": "number",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        is_valid, _ = validate_formio_data(component, {"foo": 0})

        self.assertTrue(is_valid)
