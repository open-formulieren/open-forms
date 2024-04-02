from django.test import SimpleTestCase

from rest_framework import serializers

from openforms.validations.base import BasePlugin

from ...typing import Component
from .helpers import extract_error, replace_validators_registry, validate_formio_data


class CheckboxValueSerializer(serializers.Serializer):
    value = serializers.BooleanField()


class OnlyFalseValidator(BasePlugin[bool]):
    value_serializer = CheckboxValueSerializer

    def __call__(self, value: bool, submission):
        if value is not False:
            raise serializers.ValidationError("Nope")


class CheckboxValidationTests(SimpleTestCase):

    def test_checkbox_field_required_validation(self):
        component: Component = {
            "type": "checkbox",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": ""}, "invalid"),
            ({"foo": None}, "null"),
            ({"foo": False}, "invalid"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_valid_required_checkbox(self):
        component: Component = {
            "type": "checkbox",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        is_valid, _ = validate_formio_data(component, {"foo": True})

        self.assertTrue(is_valid)

    def test_valid_optional_checkbox(self):
        component: Component = {
            "type": "checkbox",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
        }

        for value in (True, False):
            with self.subTest(checked=value):
                is_valid, _ = validate_formio_data(component, {"foo": value})

                self.assertTrue(is_valid)

    def test_checkbox_with_plugin_validator(self):
        with replace_validators_registry() as register:
            register("only_false")(OnlyFalseValidator)

            component: Component = {
                "type": "checkbox",
                "key": "foo",
                "label": "Test",
                "validate": {"plugins": ["only_false"]},
            }

            with self.subTest("valid value"):
                is_valid, _ = validate_formio_data(component, {"foo": False})

                self.assertTrue(is_valid)

            with self.subTest("invalid value"):
                is_valid, _ = validate_formio_data(component, {"foo": True})

                self.assertFalse(is_valid)
