from django.test import SimpleTestCase, tag

from hypothesis import given, strategies as st

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class PhoneNumberValidationTests(SimpleTestCase):
    def test_phonenumber_required_validation(self):
        component: Component = {
            "type": "phoneNumber",
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

    def test_pattern_validation(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "foo",
            "label": "Test",
            "validate": {
                "required": True,
                "pattern": r"06[ -]?[\d ]+",  # only allow mobile numbers
            },
        }
        data: JSONValue = {"foo": "020-123 456"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")

    def test_phonenumber_maxlength(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "foo",
            "label": "Test",
            "validate": {
                "required": True,
                "maxLength": 8,
            },
        }
        data: JSONValue = {"foo": "020123456"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "max_length")

    @given(validator=st.sampled_from(["phonenumber-international", "phonenumber-nl"]))
    def test_phonenumber_with_plugin_validator(self, validator: str):
        component: Component = {
            "type": "phoneNumber",
            "key": "foo",
            "label": "Phone",
            "validate": {"plugins": [validator]},
        }
        data: JSONValue = {"foo": "notaphonenumber"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "foo")
        self.assertEqual(error.code, "invalid")

    @tag("gh-4121")
    def test_validators_are_or_rather_than_and(self):
        component: Component = {
            "type": "phoneNumber",
            "key": "foo",
            "label": "Phone",
            "validate": {
                "plugins": [
                    "phonenumber-international",
                    "phonenumber-nl",
                ]
            },
        }
        data: JSONValue = {"foo": "0633975328"}

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    @tag("gh-4068")
    def test_multiple_with_form_builder_empty_defaults(self):
        # Our own form builder did funky stuff here by setting the defaultValue to
        # a list with `null` item. This is simulated in the submitted value.
        component: Component = {
            "type": "phoneNumber",
            "key": "manyPhonenumber",
            "label": "Optional Phone numbers",
            "validate": {"required": False},
            "multiple": True,
            "defaultValue": [""],
        }

        is_valid, _ = validate_formio_data(component, {"manyPhonenumber": [None]})

        self.assertTrue(is_valid)
