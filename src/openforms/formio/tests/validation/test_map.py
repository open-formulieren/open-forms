from django.test import SimpleTestCase

from ...typing import Component
from .helpers import extract_error, validate_formio_data


def _recursive_get_error_code(error):
    error_codes = []
    if type(error) is dict:
        for value in error.values():
            error_codes.append(_recursive_get_error_code(value))
        return error_codes

    if type(error) is list:
        for value in error:
            error_codes.append(value.code)
        return error_codes
    return error.code


class MapValidationTests(SimpleTestCase):

    def test_map_field_required_validation(self):
        component: Component = {
            "type": "map",
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

    def test_map_field_missing_keys(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = {"foo": {}}

        is_valid, errors = validate_formio_data(component, invalid_values)
        print(errors)

        geometry_type_error = extract_error(errors["foo"], "type")

        self.assertFalse(is_valid)
        self.assertIn(component["key"], errors)

        self.assertEqual(geometry_type_error.code, "required")

    def test_map_field_unknown_geometry_type(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        data = {
            "foo": {"type": "unknown-geometry-type", "coordinates": [1, 1]},
        }

        is_valid, errors = validate_formio_data(component, data)
        geometry_type_error = extract_error(errors["foo"], "type")

        self.assertFalse(is_valid)
        self.assertEqual(geometry_type_error.code, "invalid_choice")

    def test_map_field_invalid_point_geometry(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            (
                {
                    "foo": {"type": "Point"},
                },
                "required",
            ),
            (
                {
                    "foo": {"type": "Point", "coordinates": None},
                },
                "null",
            ),
            (
                {
                    "foo": {"type": "Point", "coordinates": ""},
                },
                "not_a_list",
            ),
            (
                {
                    "foo": {"type": "Point", "coordinates": 1},
                },
                "not_a_list",
            ),
            (
                {
                    "foo": {"type": "Point", "coordinates": [[1, 2]]},
                },
                ["invalid"],
            ),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)

                error = extract_error(errors["foo"], "coordinates")
                error_codes = _recursive_get_error_code(error)
                self.assertEqual(error_codes, error_code)

    def test_map_field_min_max_length_of_items_point_geometry(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            (
                {
                    "foo": {"type": "Point", "coordinates": [1]},
                },
                "min_length",
            ),
            (
                {
                    "foo": {"type": "Point", "coordinates": [1, 2, 3]},
                },
                "max_length",
            ),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                error = extract_error(errors["foo"], "coordinates")

                self.assertFalse(is_valid)
                self.assertEqual(error.code, error_code)

    def test_map_field_valid_point_geometry(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        data = {
            "foo": {"type": "Point", "coordinates": [1, 1]},
        }

        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_map_field_invalid_line_string_geometry(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            (
                {
                    "foo": {"type": "LineString"},
                },
                "required",
            ),
            (
                {
                    "foo": {"type": "LineString", "coordinates": None},
                },
                "null",
            ),
            (
                {
                    "foo": {"type": "LineString", "coordinates": ""},
                },
                "not_a_list",
            ),
            (
                {
                    "foo": {"type": "LineString", "coordinates": 1},
                },
                "not_a_list",
            ),
            (
                {
                    "foo": {"type": "LineString", "coordinates": [1, 1]},
                },
                ["not_a_list"],
            ),
            (
                {
                    "foo": {"type": "LineString", "coordinates": [[[1, 2]]]},
                },
                [["invalid"]],
            ),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)

                error = extract_error(errors["foo"], "coordinates")
                error_codes = _recursive_get_error_code(error)
                self.assertEqual(error_codes, error_code)

    def test_map_field_min_max_length_of_items_line_string_geometry(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            (
                {
                    "foo": {"type": "LineString", "coordinates": [[1]]},
                },
                "min_length",
            ),
            (
                {
                    "foo": {"type": "LineString", "coordinates": [[1, 2, 3]]},
                },
                "max_length",
            ),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                error = extract_error(errors["foo"]["coordinates"], 0)

                self.assertFalse(is_valid)
                self.assertEqual(error.code, error_code)

    def test_map_field_valid_line_string_geometry(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        data = {
            "foo": {"type": "LineString", "coordinates": [[1, 1]]},
        }
        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)

    def test_map_field_invalid_polygon_geometry(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            (
                {
                    "foo": {"type": "Polygon"},
                },
                "required",
            ),
            (
                {
                    "foo": {"type": "Polygon", "coordinates": None},
                },
                "null",
            ),
            (
                {
                    "foo": {"type": "Polygon", "coordinates": ""},
                },
                "not_a_list",
            ),
            (
                {
                    "foo": {"type": "Polygon", "coordinates": 1},
                },
                "not_a_list",
            ),
            (
                {
                    "foo": {"type": "Polygon", "coordinates": [1, 1]},
                },
                ["not_a_list"],
            ),
            (
                {
                    "foo": {"type": "Polygon", "coordinates": [[1, 1]]},
                },
                [["not_a_list"], ["not_a_list"]],
            ),
            (
                {
                    "foo": {"type": "Polygon", "coordinates": [[[[1, 2]]]]},
                },
                [[["invalid"]]],
            ),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)

                error = extract_error(errors["foo"], "coordinates")
                error_codes = _recursive_get_error_code(error)
                self.assertEqual(error_codes, error_code)

    def test_map_field_min_max_length_of_items_polygon_geometry(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            (
                {
                    "foo": {"type": "Polygon", "coordinates": [[[1]]]},
                },
                "min_length",
            ),
            (
                {
                    "foo": {"type": "Polygon", "coordinates": [[[1, 2, 3]]]},
                },
                "max_length",
            ),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                error = extract_error(errors["foo"]["coordinates"][0], 0)

                self.assertFalse(is_valid)
                self.assertEqual(error.code, error_code)

    def test_map_field_valid_polygon_geometry(self):
        component: Component = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        data = {
            "foo": {"type": "Polygon", "coordinates": [[[1, 1]]]},
        }
        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)
