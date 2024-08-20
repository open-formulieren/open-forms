from django.test import SimpleTestCase, override_settings
from django.utils.crypto import salted_hmac

from rest_framework import serializers

from openforms.contrib.brk.constants import AddressValue
from openforms.contrib.brk.validators import ValueSerializer
from openforms.submissions.models import Submission
from openforms.validations.base import BasePlugin

from ...components.utils import salt_location_message
from ...typing import AddressNLComponent
from .helpers import extract_error, replace_validators_registry, validate_formio_data


class PostcodeValidator(BasePlugin[AddressValue]):
    value_serializer = ValueSerializer

    def __call__(self, value: AddressValue, submission: Submission):
        if value["postcode"] == "1234AA":
            raise serializers.ValidationError("nope")


@override_settings(LANGUAGE_CODE="en")
class AddressNLValidationTests(SimpleTestCase):

    def test_addressNL_field_required_validation(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "Required AddressNL",
            "deriveAddress": False,
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
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "Non required AddressNL",
            "deriveAddress": False,
        }

        is_valid, _ = validate_formio_data(component, {})

        self.assertTrue(is_valid)

    def test_addressNL_field_regex_pattern_failure(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL invalid regex",
            "deriveAddress": False,
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
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL valid pattern",
            "deriveAddress": False,
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
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL missing keys",
            "deriveAddress": False,
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

            component: AddressNLComponent = {
                "key": "addressNl",
                "type": "addressNL",
                "label": "AddressNL plugin validator",
                "deriveAddress": False,
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

    def test_addressNL_field_secret_success(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL secret success",
            "deriveAddress": False,
        }

        message = "1015CJ/117/Amsterdam/Keizersgracht"
        secret = salted_hmac("location_check", value=message).hexdigest()
        data = {
            "addressNl": {
                "postcode": "1015CJ",
                "houseNumber": "117",
                "houseLetter": "",
                "houseNumberAddition": "",
                "city": "Amsterdam",
                "streetName": "Keizersgracht",
                "secretStreetCity": secret,
            }
        }

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_addressNL_field_secret_failure(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL secret failure",
            "deriveAddress": True,
        }

        data = {
            "addressNl": {
                "postcode": "1015CJ",
                "houseNumber": "117",
                "houseLetter": "",
                "houseNumberAddition": "",
                "city": "Amsterdam",
                "streetName": "Keizersgracht",
                "secretStreetCity": "invalid secret",
            }
        }

        is_valid, errors = validate_formio_data(component, data)

        secret_error = extract_error(errors["addressNl"], "non_field_errors")

        self.assertFalse(is_valid)
        self.assertEqual(secret_error.code, "invalid")

    def test_addressNL_field_missing_city(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL missing city",
            "deriveAddress": False,
        }

        data = {
            "addressNl": {
                "postcode": "1015CJ",
                "houseNumber": "117",
                "houseLetter": "",
                "houseNumberAddition": "",
                "city": "",
                "streetName": "Keizersgracht",
            }
        }

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_addressNL_field_city_street_name_no_data_found(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL secret failure",
            "deriveAddress": True,
        }

        data = {
            "addressNl": {
                "postcode": "1015CJ",
                "houseNumber": "117",
                "houseLetter": "",
                "houseNumberAddition": "",
                "city": "",
                "streetName": "",
                "secretStreetCity": salt_location_message(
                    {
                        "postcode": "1015CJ",
                        "number": "117",
                        "city": "",
                        "street_name": "",
                    }
                ),
            }
        }

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_addressNL_custom_postcode_validation_fail(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL custom postcode validation",
            "deriveAddress": False,
            "openForms": {
                "components": {
                    "postcode": {
                        "validate": {"pattern": "1017 [A-Za-z]{2}"},
                        "translatedErrors": {},
                    }
                }
            },
        }

        data = {
            "addressNl": {
                "postcode": "1015 CJ",
                "houseNumber": "117",
                "houseLetter": "",
                "houseNumberAddition": "",
                "city": "",
                "streetName": "",
            }
        }

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertEqual(errors["addressNl"]["postcode"][0].code, "invalid")

    def test_addressNL_custom_city_validation_fail(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL custom postcode validation",
            "deriveAddress": False,
            "openForms": {
                "components": {
                    "city": {
                        "validate": {"pattern": "Amsterdam"},
                        "translatedErrors": {},
                    }
                }
            },
        }

        data = {
            "addressNl": {
                "postcode": "1015 CJ",
                "houseNumber": "117",
                "houseLetter": "",
                "houseNumberAddition": "",
                "city": "Rotterdam",
                "streetName": "",
            }
        }

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertEqual(errors["addressNl"]["city"][0].code, "invalid")

    def test_addressNL_custom_postcode_and_city_validation_success(self):
        component: AddressNLComponent = {
            "key": "addressNl",
            "type": "addressNL",
            "label": "AddressNL custom postcode validation",
            "deriveAddress": False,
            "openForms": {
                "components": {
                    "postcode": {
                        "validate": {"pattern": "1017 [A-Za-z]{2}"},
                        "translatedErrors": {},
                    },
                    "city": {
                        "validate": {"pattern": "Amsterdam"},
                        "translatedErrors": {},
                    },
                }
            },
        }

        data = {
            "addressNl": {
                "postcode": "1017 CJ",
                "houseNumber": "117",
                "houseLetter": "",
                "houseNumberAddition": "",
                "city": "Amsterdam",
                "streetName": "",
            }
        }

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)
