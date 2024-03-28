from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class LicenseplateFieldValidationTests(SimpleTestCase):

    def test_licenseplatefield_required_validation(self):
        component: Component = {
            "type": "licenseplate",
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

    def test_licenseplate_pattern_validation(self):
        component: Component = {
            "type": "licenseplate",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "pattern": r"^[a-zA-Z0-9]{1,3}\\-[a-zA-Z0-9]{1,3}\\-[a-zA-Z0-9]{1,3}$",
            },
        }
        data: JSONValue = {"foo": "1-AAA-2222"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")
