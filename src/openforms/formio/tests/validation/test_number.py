from django.test import SimpleTestCase

from rest_framework import serializers

from openforms.validations.base import BasePlugin

from ...typing import Component
from .helpers import extract_error, replace_validators_registry, validate_formio_data


class NumberValueSerializer(serializers.Serializer):
    value = serializers.FloatField()


class GT5Validator(BasePlugin[int | float]):
    value_serializer = NumberValueSerializer

    def __call__(self, value: int | float, submission):
        if not value > 5:
            raise serializers.ValidationError("Nope")


class NumberValidationTests(SimpleTestCase):
    def test_number_min_value(self):
        component: Component = {
            "type": "number",
            "key": "foo",
            "label": "Test",
            "validate": {
                "min": -3.5,
            },
        }

        is_valid, errors = validate_formio_data(component, {"foo": -5.2})

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "min_value")

    def test_number_min_value_with_non_required_value(self):
        component: Component = {
            "type": "number",
            "key": "foo",
            "label": "Test",
            "validate": {"max": 10},
        }

        is_valid, _ = validate_formio_data(component, {})

        self.assertTrue(is_valid)

    def test_zero_is_accepted(self):
        component: Component = {
            "type": "number",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        is_valid, _ = validate_formio_data(component, {"foo": 0})

        self.assertTrue(is_valid)

    def test_number_with_plugin_validator(self):
        with replace_validators_registry() as register:
            register("gt_5")(GT5Validator)

            component: Component = {
                "type": "number",
                "key": "foo",
                "label": "Test",
                "validate": {"plugins": ["gt_5"]},
            }

            with self.subTest("valid value"):
                is_valid, _ = validate_formio_data(component, {"foo": 10})

                self.assertTrue(is_valid)

            with self.subTest("invalid value"):
                is_valid, _ = validate_formio_data(component, {"foo": 1})

                self.assertFalse(is_valid)

    def test_number_required_validation(self):
        component: Component = {
            "type": "number",
            "key": "foo",
            "label": "Test",
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

    def test_number_optional_allows_empty(self):
        component: Component = {
            "type": "number",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
        }

        is_valid, _ = validate_formio_data(component, {"foo": None})

        self.assertTrue(is_valid)
