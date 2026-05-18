from django.test import SimpleTestCase, tag

from hypothesis import given, strategies as st

from openforms.typing import JSONValue

from ...typing import TextFieldComponent
from .helpers import extract_error, validate_formio_data


class TextFieldValidationTests(SimpleTestCase):
    def test_textfield_required_validation(self):
        component: TextFieldComponent = {
            "type": "textfield",
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

    def test_hidden_textfield_required_validation(self):
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "foo.bar",
            "label": "Test",
            "validate": {"required": True},
            "hidden": True,
        }

        is_valid = validate_formio_data(component, {"foo": {"bar": ""}})

        self.assertTrue(is_valid)

    def test_textfield_max_length(self):
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "foo",
            "label": "Test",
            "validate": {"maxLength": 3},
        }

        is_valid, errors = validate_formio_data(component, {"foo": "barbaz"})

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "max_length")

    @tag("gh-3977")
    def test_textfield_regex_housenumber(self):
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "houseNumber",
            "label": "House number",
            "validate": {"pattern": r"[0-9]{1,5}"},
        }
        data: JSONValue = {"houseNumber": "<div>injection</div>"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "houseNumber")
        self.assertEqual(error.code, "invalid")

    @tag("gh-3977")
    def test_textfield_regex_housenumber_addition(self):
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "houseNumberAddition",
            "label": "House number",
            "validate": {"pattern": r"^[a-zA-Z0-9]{1,4}$"},
        }
        data: JSONValue = {"houseNumberAddition": "<div>injection</div>"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "houseNumberAddition")
        self.assertEqual(error.code, "invalid")

    def test_multiple(self):
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "numbers",
            "label": "House number",
            "multiple": True,
            "validate": {"pattern": r"\d+"},
            "defaultValue": [],
        }
        data: JSONValue = {"numbers": ["42", "notnumber"]}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = errors["numbers"][1][0]
        self.assertEqual(error.code, "invalid")

        with self.subTest("valid item"):
            self.assertNotIn(0, errors["numbers"])

    @tag("gh-4068")
    def test_multiple_with_form_builder_empty_defaults(self):
        # Our own form builder did funky stuff here by setting the defaultValue to
        # a list with `null` item. This is simulated in the submitted value.
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "manyTextfield",
            "label": "Optional Text fields",
            "validate": {"required": False},
            "multiple": True,
            "defaultValue": [""],
        }

        is_valid, _ = validate_formio_data(component, {"manyTextfield": [None]})

        self.assertTrue(is_valid)

    @given(validator=st.sampled_from(["phonenumber-international", "phonenumber-nl"]))
    def test_textfield_with_plugin_validator(self, validator: str):
        component: TextFieldComponent = {
            "type": "textfield",
            "key": "foo",
            "label": "House number",
            "validate": {"plugins": [validator]},
        }
        data: JSONValue = {"foo": "notaphonenumber"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "foo")
        self.assertEqual(error.code, "invalid")
