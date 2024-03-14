from django.test import SimpleTestCase

from rest_framework import serializers

from openforms.typing import JSONValue
from openforms.validations.base import BasePlugin

from ...typing import Component
from .helpers import extract_error, replace_validators_registry, validate_formio_data


class NoLeading1Validator(BasePlugin[str]):
    def __call__(self, value: str, submission):
        if value.startswith("1"):
            raise serializers.ValidationError("nope")


class BSNValidationTests(SimpleTestCase):

    def test_bsn_field_required_validation(self):
        component: Component = {
            "type": "bsn",
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

    def test_maxlength(self):
        component: Component = {
            "type": "bsn",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True, "maxLength": 5},
        }
        data: JSONValue = {"foo": "123456"}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        error = extract_error(errors, "foo")
        self.assertEqual(error.code, "max_length")

    # TODO
    # def test_elfproef(self):
    #     pass

    def test_bsn_with_plugin_validator(self):
        with replace_validators_registry() as register:
            register("no_leading_1")(NoLeading1Validator)

            component: Component = {
                "type": "bsn",
                "key": "foo",
                "label": "Test",
                "validate": {"plugins": ["no_leading_1"]},
            }

            with self.subTest("valid value"):
                is_valid, _ = validate_formio_data(component, {"foo": "223456780"})

                self.assertTrue(is_valid)

            with self.subTest("invalid value"):
                is_valid, _ = validate_formio_data(component, {"foo": "123456782"})

                self.assertFalse(is_valid)
