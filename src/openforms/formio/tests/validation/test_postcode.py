from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class PostcodeFieldValidationTests(SimpleTestCase):

    def test_postcodefield_required_validation(self):
        component: Component = {
            "type": "postcode",
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

    def test_postcode_pattern_validation(self):
        component: Component = {
            "type": "postcode",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "pattern": r"^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$",
            },
        }
        data: JSONValue = {"foo": "1234A"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")

    def test_multiple(self):
        component: Component = {
            "type": "postcode",
            "key": "foo",
            "label": "Test",
            "multiple": False,
        }
        data: JSONValue = {"foo": ["1234AA", "2341MM"]}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")
