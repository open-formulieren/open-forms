from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class IbanFieldValidationTests(SimpleTestCase):
    def test_valid_required_ibanfield(self):
        component: Component = {
            "type": "iban",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": True},
        }

        data: JSONValue = {"foo": "NL56 INGB 0705 0051 00"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertTrue(is_valid)
        self.assertDictEqual(errors, {})

    def test_valid_non_required_ibanfield(self):
        component: Component = {
            "type": "iban",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": False},
        }
        data: JSONValue = {"foo": ""}

        is_valid, errors = validate_formio_data(component, data)

        self.assertTrue(is_valid)
        self.assertDictEqual(errors, {})

    def test_invalid_required_ibanfield(self):
        component: Component = {
            "type": "iban",
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
            "type": "iban",
            "key": "foo",
            "label": "Test",
            "multiple": True,
        }

        data: JSONValue = {
            "foo": [" RO09 BCYP 0000 1112 3456 5678", "RO09 BCYP 0000 0012 3456 7890"]
        }

        is_valid, errors = validate_formio_data(component, data)

        self.assertTrue(is_valid)
        self.assertDictEqual(errors, {})

    def test_multiple_disabled(self):
        component: Component = {
            "type": "iban",
            "key": "foo",
            "label": "Test",
            "multiple": False,
        }

        data: JSONValue = {
            "foo": [" RO09 BCYP 0000 1112 3456 5678", "RO09 BCYP 0000 0012 3456 7890"]
        }

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")
