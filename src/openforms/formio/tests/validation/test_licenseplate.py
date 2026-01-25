from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class LicenseplateFieldValidationTests(SimpleTestCase):
    def test_valid_non_required_licenseplatefield(self):
        component: Component = {
            "type": "licenseplate",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "required": False,
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$",
            },
        }

        data: JSONValue = {"foo": "1-AAA-BB"}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_valid_required_licenseplatefield(self):
        component: Component = {
            "type": "licenseplate",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "required": True,
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$",
            },
        }

        data: JSONValue = {"foo": "1-AAA-BB"}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_invalid_required_licenseplatefield(self):
        component: Component = {
            "type": "licenseplate",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "required": True,
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$",
            },
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": "wrong input"}, "invalid"),
            ({"foo": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_invalid_non_required_licenseplatefield(self):
        component: Component = {
            "type": "licenseplate",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "required": False,
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$",
            },
        }

        invalid_values = [
            ({"foo": "AAAA-8-A"}, "invalid"),
            ({"foo": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_valid_licenseplatefield_pattern(self):
        component: Component = {
            "type": "licenseplate",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$",
            },
        }

        data: JSONValue = {"foo": "1-AAA-BB"}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_invalid_licenseplatefield_pattern(self):
        component: Component = {
            "type": "licenseplate",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$",
            },
        }

        data: JSONValue = {"foo": "1-AAA-2222"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")

    def test_multiple_enabled(self):
        component: Component = {
            "type": "licenseplate",
            "key": "foo",
            "label": "Foo",
            "multiple": True,
            "validate": {
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$",
            },
            "defaultValue": [],
        }

        data: JSONValue = {"foo": ["1-AAA-222", "33-A-AF6"]}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_multiple_disabled(self):
        component: Component = {
            "type": "licenseplate",
            "key": "foo",
            "label": "Foo",
            "multiple": False,
            "validate": {
                "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$",
            },
        }

        data: JSONValue = {"foo": ["1-AAA-222", "33-A-AF5"]}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")
