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
                "url": "",
                "json": "",
                "custom": "",
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
                "resource": "",
            },
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
