from django.test import SimpleTestCase

from rest_framework import serializers

from openforms.validations.base import BasePlugin

from ...typing import Component
from .helpers import extract_error, replace_validators_registry, validate_formio_data


class CurrencyValueSerializer(serializers.Serializer):
    value = serializers.FloatField()


class GT5Validator(BasePlugin[int | float]):
    value_serializer = CurrencyValueSerializer

    def __call__(self, value: int | float, submission):
        if not value > 5:
            raise serializers.ValidationError("Nope")


class CurrencyFieldValidationTests(SimpleTestCase):

    def test_currencyfield_required_validation(self):
        component: Component = {
            "type": "currency",
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

    def test_min_max_values(self):
        component: Component = {
            "type": "currency",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "required": False,
                "min": 10.7,
                "max": 15,
            },
        }

        invalid_values = [
            ({"foo": 0}, "min_value"),
            ({"foo": 9}, "min_value"),
            ({"foo": 17}, "max_value"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_currency_with_plugin_validator(self):
        with replace_validators_registry() as register:
            register("gt_5")(GT5Validator)

            component: Component = {
                "type": "currency",
                "key": "foo",
                "label": "Test",
                "validate": {"plugins": ["gt_5"]},
            }

            with self.subTest("valid value"):
                is_valid, _ = validate_formio_data(component, {"foo": 10})

                self.assertTrue(is_valid)

            with self.subTest("invalid value"):
                is_valid, _ = validate_formio_data(component, {"foo": 1.5})

                self.assertFalse(is_valid)

    def test_currency_required_validation(self):
        component: Component = {
            "type": "currency",
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

    def test_currency_optional_allows_empty(self):
        component: Component = {
            "type": "currency",
            "key": "foo",
            "label": "Test",
            "validate": {"required": False},
        }

        is_valid, _ = validate_formio_data(component, {"foo": None})

        self.assertTrue(is_valid)
