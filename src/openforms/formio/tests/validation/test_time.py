from django.test import SimpleTestCase

from openforms.typing import JSONValue

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class TimeFieldValidationTests(SimpleTestCase):
    def test_timefield_required_validation(self):
        component: Component = {
            "type": "time",
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

    def test_min_max_time(self):
        component: Component = {
            "type": "time",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "required": False,
                "minTime": "10:00",  # type:ignore
                "maxTime": "12:00",  # type:ignore
            },
        }

        invalid_values = [
            ({"foo": "09:10"}, "min_value"),
            ({"foo": "09:59:59"}, "min_value"),
            ({"foo": "12:10"}, "max_value"),
            ({"foo": "12:00:01"}, "max_value"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

        with self.subTest("valid value"):
            is_valid, _ = validate_formio_data(component, {"foo": "11:00"})

            self.assertTrue(is_valid)

    def test_only_min_time(self):
        component: Component = {
            "type": "time",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "required": False,
                "minTime": "10:00",  # type:ignore
            },
        }

        invalid_values: list[tuple[JSONValue, str]] = [
            ({"foo": "09:10"}, "min_value"),
            ({"foo": "09:59:59"}, "min_value"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

        valid_values = (
            "10:00",
            "10:00:01",
            "11:00",
        )
        for value in valid_values:
            with self.subTest(valid_value=value):
                is_valid, _ = validate_formio_data(component, {"foo": value})

                self.assertTrue(is_valid)

    def test_only_max_time(self):
        component: Component = {
            "type": "time",
            "key": "foo",
            "label": "Foo",
            "validate": {
                "required": False,
                "maxTime": "12:00",  # type:ignore
            },
        }

        invalid_values: list[tuple[JSONValue, str]] = [
            ({"foo": "12:10"}, "max_value"),
            ({"foo": "12:00:01"}, "max_value"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)

        valid_values = (
            "11:59",
            "11:59:59",
            "12:00",
        )
        for value in valid_values:
            with self.subTest(valid_value=value):
                is_valid, _ = validate_formio_data(component, {"foo": value})

                self.assertTrue(is_valid)

    def test_multiple(self):
        component: Component = {
            "type": "time",
            "key": "foo",
            "label": "Test",
            "multiple": False,
        }
        data: JSONValue = {"foo": ["11:00", "12:00"]}

        is_valid, errors = validate_formio_data(component, data)

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)
        error = extract_error(errors, component["key"])
        self.assertEqual(error.code, "invalid")

    def test_empty_default_value(self):
        component: Component = {
            "type": "time",
            "key": "time",
            "label": "Optional time",
            "validate": {"required": False},
        }

        is_valid, _ = validate_formio_data(component, {"time": ""})

        self.assertTrue(is_valid)

    def test_min_max_time_different_days(self):
        # Special validation logic - if both min and max time are provided and
        # min is > max, then it is assumed they are swapped because they cross
        # mignight
        component: Component = {
            "type": "time",
            "key": "time",
            "label": "Optional time",
            "validate": {
                "minTime": "20:00",  # type:ignore
                "maxTime": "04:00",  # type:ignore
            },
        }

        with self.subTest("valid - day 1"):
            valid_value = "23:00"

            is_valid, _ = validate_formio_data(component, {"time": valid_value})

            self.assertTrue(is_valid)

        with self.subTest("valid - day 2"):
            valid_value = "04:00"

            is_valid, _ = validate_formio_data(component, {"time": valid_value})

            self.assertTrue(is_valid)

        with self.subTest("invalid 1"):
            invalid_value = "18:00"

            is_valid, _ = validate_formio_data(component, {"time": invalid_value})

            self.assertFalse(is_valid)

        with self.subTest("invalid 2"):
            invalid_value = "04:01"

            is_valid, _ = validate_formio_data(component, {"time": invalid_value})

            self.assertFalse(is_valid)
