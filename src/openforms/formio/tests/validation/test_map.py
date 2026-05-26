from django.test import SimpleTestCase

from ...typing import MapComponent
from .helpers import extract_error, validate_formio_data


class MapValidationTests(SimpleTestCase):
    def test_map_field_required_validation(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
            "validate": {"required": True},
        }

        invalid_values_with_expected_error_code = [
            ({}, "required"),
            ({"foo": None}, "null"),
        ]

        for (
            invalid_value,
            expected_error_code,
        ) in invalid_values_with_expected_error_code:
            with self.subTest(data=invalid_value):
                is_valid, errors = validate_formio_data(component, invalid_value)

                self.assertFalse(is_valid)
                self.assertIn("foo", errors)

                error = extract_error(errors, "foo")

                self.assertEqual(error.code, expected_error_code)

    def test_map_field_unknown_type(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        invalid_value = {
            "foo": {"type": "unknown-geometry-type", "coordinates": [1, 1]},
        }

        is_valid, errors = validate_formio_data(component, invalid_value)

        self.assertFalse(is_valid)
        self.assertIn("foo", errors)
        self.assertIn("type", errors["foo"])

        geometry_type_error = extract_error(errors["foo"], "type")

        self.assertEqual(geometry_type_error.code, "invalid_choice")

    def test_map_field_point_geometry_missing_coordinates(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        invalid_value = {
            "foo": {"type": "Point"},
        }

        is_valid, errors = validate_formio_data(component, invalid_value)

        self.assertFalse(is_valid)
        self.assertIn("foo", errors)
        self.assertIn("coordinates", errors["foo"])

        coordinates_error = extract_error(errors["foo"], "coordinates")

        self.assertEqual(coordinates_error.code, "required")

    def test_map_field_point_geometry_invalid_coordinates(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        with self.subTest(case="Using non-array values for coordinates"):
            invalid_values_with_expected_error_code = [
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
            ]

            for (
                invalid_value,
                expected_error_code,
            ) in invalid_values_with_expected_error_code:
                with self.subTest(data=invalid_value):
                    is_valid, errors = validate_formio_data(component, invalid_value)

                    self.assertFalse(is_valid)
                    self.assertIn("foo", errors)
                    self.assertIn("coordinates", errors["foo"])

                    coordinates_error = extract_error(errors["foo"], "coordinates")

                    self.assertEqual(coordinates_error.code, expected_error_code)

        with self.subTest(case="Coordinates array value goes a level too deep"):
            invalid_value = {
                "foo": {"type": "Point", "coordinates": [[1, 2]]},
            }

            is_valid, errors = validate_formio_data(component, invalid_value)

            self.assertFalse(is_valid)
            self.assertIn("foo", errors)
            self.assertIn("coordinates", errors["foo"])
            # There is an error inside the coordinates array
            self.assertIn(0, errors["foo"]["coordinates"])

            coordinates_error = extract_error(errors["foo"], "coordinates")

            self.assertEqual(coordinates_error[0].code, "invalid")

    def test_map_field_point_geometry_length_of_coordinates(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        with self.subTest(case="Less than 2 values in coordinates"):
            invalid_values = [
                {
                    "foo": {"type": "Point", "coordinates": []},
                },
                {
                    "foo": {"type": "Point", "coordinates": [1]},
                },
            ]

            for invalid_value in invalid_values:
                with self.subTest(data=invalid_value):
                    is_valid, errors = validate_formio_data(component, invalid_value)

                    self.assertFalse(is_valid)
                    self.assertIn("foo", errors)
                    self.assertIn("coordinates", errors["foo"])

                    coordinates_error = extract_error(errors["foo"], "coordinates")

                    self.assertEqual(coordinates_error.code, "min_length")

        with self.subTest(case="More than 2 values in coordinates"):
            invalid_value = {
                "foo": {"type": "Point", "coordinates": [1, 2, 3]},
            }

            is_valid, errors = validate_formio_data(component, invalid_value)

            self.assertFalse(is_valid)
            self.assertIn("foo", errors)
            self.assertIn("coordinates", errors["foo"])

            coordinates_error = extract_error(errors["foo"], "coordinates")

            self.assertEqual(coordinates_error.code, "max_length")

    def test_map_field_valid_point_geometry(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        valid_value = {
            "foo": {"type": "Point", "coordinates": [1, 1]},
        }

        is_valid, _ = validate_formio_data(component, valid_value)

        self.assertTrue(is_valid)

    def test_map_field_line_string_geometry_missing_coordinates(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        invalid_value = {
            "foo": {"type": "LineString"},
        }

        is_valid, errors = validate_formio_data(component, invalid_value)

        self.assertFalse(is_valid)
        self.assertIn("foo", errors)
        self.assertIn("coordinates", errors["foo"])

        coordinates_error = extract_error(errors["foo"], "coordinates")

        self.assertEqual(coordinates_error.code, "required")

    def test_map_field_line_string_geometry_invalid_coordinates(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        with self.subTest(case="Using non-array values for coordinates"):
            invalid_values_with_expected_error_code = [
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
            ]

            for (
                invalid_value,
                expected_error_code,
            ) in invalid_values_with_expected_error_code:
                with self.subTest(data=invalid_value):
                    is_valid, errors = validate_formio_data(component, invalid_value)

                    self.assertFalse(is_valid)
                    self.assertIn("foo", errors)
                    self.assertIn("coordinates", errors["foo"])

                    coordinates_error = extract_error(errors["foo"], "coordinates")

                    self.assertEqual(coordinates_error.code, expected_error_code)

        with self.subTest(case="Using an 1 dimensional array for coordinates"):
            invalid_value = {
                "foo": {"type": "LineString", "coordinates": [1, 1]},
            }

            is_valid, errors = validate_formio_data(component, invalid_value)

            self.assertFalse(is_valid)
            self.assertIn("foo", errors)
            self.assertIn("coordinates", errors["foo"])
            # Error inside coordinates value
            self.assertIn(0, errors["foo"]["coordinates"])

            coordinates_error = extract_error(errors["foo"], "coordinates")

            self.assertEqual(coordinates_error[0].code, "not_a_list")

        with self.subTest(case="Using a 3 dimensional array for coordinates"):
            invalid_value = {
                "foo": {"type": "LineString", "coordinates": [[[1, 2]]]},
            }

            is_valid, errors = validate_formio_data(component, invalid_value)

            self.assertFalse(is_valid)
            self.assertIn("foo", errors)
            self.assertIn("coordinates", errors["foo"])
            # Error inside coordinates value
            self.assertIn(0, errors["foo"]["coordinates"])
            self.assertIn(0, errors["foo"]["coordinates"][0])

            coordinates_error = extract_error(errors["foo"], "coordinates")

            self.assertEqual(coordinates_error[0][0].code, "invalid")

    def test_map_field_line_string_geometry_length_of_coordinates(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        with self.subTest(case="Less than 2 values in coordinates"):
            invalid_values = [
                {
                    "foo": {"type": "LineString", "coordinates": [[]]},
                },
                {
                    "foo": {"type": "LineString", "coordinates": [[1]]},
                },
            ]

            for invalid_value in invalid_values:
                with self.subTest(data=invalid_value):
                    is_valid, errors = validate_formio_data(component, invalid_value)

                    self.assertFalse(is_valid)
                    self.assertIn("foo", errors)
                    self.assertIn("coordinates", errors["foo"])
                    # Error inside coordinates value
                    self.assertIn(0, errors["foo"]["coordinates"])

                    coordinates_error = extract_error(errors["foo"], "coordinates")

                    self.assertEqual(coordinates_error[0].code, "min_length")

        with self.subTest(case="More than 2 values in coordinates"):
            invalid_value = {
                "foo": {"type": "LineString", "coordinates": [[1, 2, 3]]},
            }

            is_valid, errors = validate_formio_data(component, invalid_value)

            self.assertFalse(is_valid)
            self.assertIn("foo", errors)
            self.assertIn("coordinates", errors["foo"])
            # Error inside coordinates value
            self.assertIn(0, errors["foo"]["coordinates"])

            coordinates_error = extract_error(errors["foo"], "coordinates")

            self.assertEqual(coordinates_error[0].code, "max_length")

    def test_map_field_valid_line_string_geometry(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        valid_value = {
            "foo": {"type": "LineString", "coordinates": [[1, 1]]},
        }

        is_valid, _ = validate_formio_data(component, valid_value)

        self.assertTrue(is_valid)

    def test_map_field_polygon_geometry_missing_coordinates(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        invalid_value = {
            "foo": {"type": "Polygon"},
        }

        is_valid, errors = validate_formio_data(component, invalid_value)

        self.assertFalse(is_valid)
        self.assertIn("foo", errors)
        self.assertIn("coordinates", errors["foo"])

        coordinates_error = extract_error(errors["foo"], "coordinates")

        self.assertEqual(coordinates_error.code, "required")

    def test_map_field_polygon_geometry_invalid_coordinates(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        with self.subTest(case="Using non-array values for coordinates"):
            invalid_values_with_expected_error_code = [
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
            ]

            for (
                invalid_value,
                expected_error_code,
            ) in invalid_values_with_expected_error_code:
                with self.subTest(data=invalid_value):
                    is_valid, errors = validate_formio_data(component, invalid_value)

                    self.assertFalse(is_valid)
                    self.assertIn("foo", errors)
                    self.assertIn("coordinates", errors["foo"])

                    coordinates_error = extract_error(errors["foo"], "coordinates")

                    self.assertEqual(coordinates_error.code, expected_error_code)

        with self.subTest(case="Using an 1 dimensional array for coordinates"):
            invalid_value = {
                "foo": {"type": "Polygon", "coordinates": [1, 1]},
            }

            is_valid, errors = validate_formio_data(component, invalid_value)

            self.assertFalse(is_valid)
            self.assertIn("foo", errors)
            self.assertIn("coordinates", errors["foo"])
            # Error inside coordinates value
            self.assertIn(0, errors["foo"]["coordinates"])

            coordinates_error = extract_error(errors["foo"], "coordinates")

            self.assertEqual(coordinates_error[0].code, "not_a_list")

        with self.subTest(case="Using an 2 dimensional array for coordinates"):
            invalid_value = {
                "foo": {"type": "Polygon", "coordinates": [[1, 1]]},
            }

            is_valid, errors = validate_formio_data(component, invalid_value)

            self.assertFalse(is_valid)
            self.assertIn("foo", errors)
            self.assertIn("coordinates", errors["foo"])
            # Error inside coordinates value
            self.assertIn(0, errors["foo"]["coordinates"])
            self.assertIn(0, errors["foo"]["coordinates"][0])
            self.assertIn(1, errors["foo"]["coordinates"][0])

            coordinates_error = extract_error(errors["foo"], "coordinates")

            self.assertEqual(coordinates_error[0][0].code, "not_a_list")
            self.assertEqual(coordinates_error[1][0].code, "not_a_list")

        with self.subTest(case="Using an 4 dimensional array for coordinates"):
            invalid_value = {
                "foo": {"type": "Polygon", "coordinates": [[[[1, 2]]]]},
            }

            is_valid, errors = validate_formio_data(component, invalid_value)

            self.assertFalse(is_valid)
            self.assertIn("foo", errors)
            self.assertIn("coordinates", errors["foo"])
            # Error inside coordinates value
            self.assertIn(0, errors["foo"]["coordinates"])
            self.assertIn(0, errors["foo"]["coordinates"][0])
            self.assertIn(0, errors["foo"]["coordinates"][0][0])

            coordinates_error = extract_error(errors["foo"], "coordinates")

            self.assertEqual(coordinates_error[0][0][0].code, "invalid")

    def test_map_field_polygon_geometry_length_of_coordinates(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        with self.subTest(case="Using less than 2 values for coordinates"):
            invalid_values = [
                {
                    "foo": {"type": "Polygon", "coordinates": [[[]]]},
                },
                {
                    "foo": {"type": "Polygon", "coordinates": [[[1]]]},
                },
            ]

            for invalid_value in invalid_values:
                with self.subTest(data=invalid_value):
                    is_valid, errors = validate_formio_data(component, invalid_value)

                    self.assertFalse(is_valid)
                    self.assertIn("foo", errors)
                    self.assertIn("coordinates", errors["foo"])
                    # Error inside coordinates value
                    self.assertIn(0, errors["foo"]["coordinates"])
                    self.assertIn(0, errors["foo"]["coordinates"][0])

                    coordinates_error = extract_error(errors["foo"], "coordinates")

                    self.assertEqual(coordinates_error[0][0].code, "min_length")

        with self.subTest(case="Using more than 2 values for coordinates"):
            invalid_value = {
                "foo": {"type": "Polygon", "coordinates": [[[1, 2, 3]]]},
            }
            is_valid, errors = validate_formio_data(component, invalid_value)

            self.assertFalse(is_valid)
            self.assertIn("foo", errors)
            self.assertIn("coordinates", errors["foo"])
            # Error inside coordinates value
            self.assertIn(0, errors["foo"]["coordinates"])
            self.assertIn(0, errors["foo"]["coordinates"][0])

            coordinates_error = extract_error(errors["foo"], "coordinates")

            self.assertEqual(coordinates_error[0][0].code, "max_length")

    def test_map_field_valid_polygon_geometry(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "foo",
            "interactions": {"marker": True, "polyline": False, "polygon": False},
            "useConfigDefaultMapSettings": False,
        }

        data = {
            "foo": {"type": "Polygon", "coordinates": [[[1, 1]]]},
        }
        is_valid, _ = validate_formio_data(component, data)

        self.assertTrue(is_valid)
