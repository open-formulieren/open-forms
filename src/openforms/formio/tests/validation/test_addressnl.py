from django.test import SimpleTestCase

from rest_framework import serializers

from openforms.contrib.brk.constants import AddressValue
from openforms.contrib.brk.validators import ValueSerializer
from openforms.submissions.models import Submission
from openforms.validations.base import BasePlugin

from ...typing import Component
from .helpers import extract_error, replace_validators_registry, validate_formio_data


class PostcodeValidator(BasePlugin[AddressValue]):
    value_serializer = ValueSerializer

    def __call__(self, value: AddressValue, submission: Submission):
        if value["postcode"] == "1234AA":
            raise serializers.ValidationError("nope")


class AddressNLValidationTests(SimpleTestCase):

    def test_addressNL_field_required_validation(self):
        component: Component = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "Required AddressNL",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"addressNl": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_addressNL_field_non_required_validation(self):
        component: Component = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "Non required AddressNL",
        }

        is_valid, _ = validate_formio_data(component, {})

        self.assertTrue(is_valid)

    def test_addressNL_field_regex_pattern_failure(self):
        component: Component = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL invalid regex",
        }

        invalid_values = {
            "addressNl": {
                "postcode": "123456wrong",
                "houseNumber": "",
                "houseLetter": "A",
                "houseNumberAddition": "",
            }
        }

        is_valid, errors = validate_formio_data(component, invalid_values)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)

        error = extract_error(errors["addressNl"], "postcode")

        self.assertEqual(error.code, "invalid")

    def test_addressNL_field_regex_pattern_success(self):
        component: Component = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL valid pattern",
        }

        data = {
            "addressNl": {
                "postcode": "1234AA",
                "houseNumber": "2",
                "houseLetter": "A",
                "houseNumberAddition": "",
            }
        }

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_missing_keys(self):
        component: Component = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL missing keys",
        }

        invalid_values = {
            "addressNl": {
                "houseLetter": "A",
            }
        }

        is_valid, errors = validate_formio_data(component, invalid_values)

        postcode_error = extract_error(errors["addressNl"], "postcode")
        house_number_error = extract_error(errors["addressNl"], "houseNumber")

        self.assertFalse(is_valid)
        self.assertEqual(postcode_error.code, "required")
        self.assertEqual(house_number_error.code, "required")

    def test_plugin_validator(self):
        with replace_validators_registry() as register:
            register("postcode_validator")(PostcodeValidator)

            component: Component = {
                "key": "addressNl",
                "type": "addressNL",
                "label": "AddressNL plugin validator",
                "validate": {"plugins": ["postcode_validator"]},
            }

            with self.subTest("valid value"):
                is_valid, _ = validate_formio_data(
                    component,
                    {
                        "addressNl": {
                            "postcode": "9877AA",
                            "houseNumber": "3",
                            "houseLetter": "A",
                            "houseNumberAddition": "",
                        }
                    },
                )

                self.assertTrue(is_valid)

            with self.subTest("invalid value"):
                is_valid, _ = validate_formio_data(
                    component,
                    {
                        "addressNl": {
                            "postcode": "1234AA",
                            "houseNumber": "3",
                            "houseLetter": "A",
                            "houseNumberAddition": "",
                        }
                    },
                )

                self.assertFalse(is_valid)
