from django.test import SimpleTestCase, tag

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class TextAreaValidationTests(SimpleTestCase):
    def test_textarea_required_validation(self):
        component: Component = {
            "type": "textarea",
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

    def test_textarea_max_length(self):
        component: Component = {
            "type": "textarea",
            "key": "foo",
            "label": "Test",
            "validate": {"maxLength": 3},
        }

        is_valid, errors = validate_formio_data(component, {"foo": "barbaz"})

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "max_length")

    def test_multiple(self):
        component: Component = {
            "type": "textarea",
            "key": "foo",
            "label": "Test",
            "multiple": False,
        }
        data: JSONValue = {"foo": ["test a value", "another value"]}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")

    @tag("gh-4068")
    def test_multiple_with_form_builder_empty_defaults(self):
        # Our own form builder did funky stuff here by setting the defaultValue to
        # a list with `null` item. This is simulated in the submitted value.
        component: Component = {
            "type": "textarea",
            "key": "manyTextarea",
            "label": "Optional textareas",
            "validate": {"required": False},
            "multiple": True,
            "defaultValue": [""],
        }

        is_valid, _ = validate_formio_data(component, {"manyTextarea": [None]})

        self.assertTrue(is_valid)
