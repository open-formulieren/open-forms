from django.test import SimpleTestCase, tag

from ...typing import DateComponent
from .helpers import extract_error, validate_formio_data


class DateFieldValidationTests(SimpleTestCase):

    def test_datefield_required_validation(self):
        component: DateComponent = {
            "type": "date",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": None}, "null"),
            ({"foo": ""}, "required"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    def test_min_max_date(self):
        component: DateComponent = {
            "type": "date",
            "key": "foo",
            "label": "Foo",
            "validate": {"required": False},
            "datePicker": {
                "minDate": "2024-03-10",
                "maxDate": "2025-03-10",
            },
        }

        invalid_values = [
            ({"foo": "2023-01-01"}, "min_value"),
            ({"foo": "2025-12-30"}, "max_value"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

    @tag("gh-4068")
    def test_empty_default_value(self):
        component: DateComponent = {
            "type": "date",
            "key": "date",
            "label": "Optional date",
            "validate": {"required": False},
        }

        is_valid, _ = validate_formio_data(component, {"date": ""})

        self.assertTrue(is_valid)
