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

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_valid_non_required_ibanfield(self):
        component: Component = {
            "type": "iban",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": False},
        }
        data: JSONValue = {"foo": ""}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

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
            ({"foo": "NLKI12345678"}, "invalid"),
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
            "defaultValue": [],
        }

        data: JSONValue = {"foo": ["NL02ABNA0123456789", "NL14 ABNA 1238 8878 00"]}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_multiple_disabled(self):
        component: Component = {
            "type": "iban",
            "key": "foo",
            "label": "Test",
            "multiple": False,
        }

        data: JSONValue = {"foo": ["NL02ABNA0123456789", "NL14 ABNA 1238 8878 00"]}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")
