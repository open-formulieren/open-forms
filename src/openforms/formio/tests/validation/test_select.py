from django.test import SimpleTestCase

from ...typing import SelectComponent
from .helpers import extract_error, validate_formio_data


class SelectValidationTests(SimpleTestCase):
    def test_select_field_required_validation(self):
        component: SelectComponent = {
            "type": "select",
            "key": "foo",
            "label": "Test",
            "data": {
                "values": [
                    {
                        "label": "first",
                        "value": "first",
                        "openForms": {"translations": {}},
                    },
                    {
                        "label": "second",
                        "value": "second",
                        "openForms": {"translations": {}},
                    },
                ],
            },
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": None}, "null"),
            ({"foo": ["first"]}, "invalid_choice"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_optional_single_select(self):
        component: SelectComponent = {
            "type": "select",
            "key": "foo",
            "label": "Test",
            "data": {
                "values": [
                    {
                        "label": "A",
                        "value": "a",
                    },
                    {
                        "label": "B",
                        "value": "b",
                    },
                ],
            },
            "validate": {"required": False},
        }

        is_valid, _ = validate_formio_data(component, {"foo": ""})

        self.assertTrue(is_valid)

    def test_required_multiple_select(self):
        component: SelectComponent = {
            "type": "select",
            "key": "foo",
            "label": "Test",
            "multiple": True,
            "data": {
                "values": [
                    {
                        "label": "A",
                        "value": "a",
                    },
                    {
                        "label": "B",
                        "value": "b",
                    },
                ],
            },
            "validate": {"required": True},
            "defaultValue": [],
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": None}, "null"),
            ({"foo": []}, "empty"),
            ({"foo": [""]}, "invalid_choice"),
            ({"foo": "b"}, "not_a_list"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)
