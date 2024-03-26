from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class IbanFieldValidationTests(SimpleTestCase):

    def test_ibanfield_required_validation(self):
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

    def test_multiple(self):
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
