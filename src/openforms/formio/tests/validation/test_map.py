from django.test import SimpleTestCase

from ...typing import MapComponent
from .helpers import extract_error, validate_formio_data


class MapValidationTests(SimpleTestCase):

    def test_map_field_required_validation(self):
        component: MapComponent = {
            "type": "map",
            "key": "foo",
            "label": "Test",
            "validate": {"required": True},
        }

        invalid_values = [
            ({}, "required"),
            ({"foo": ""}, "not_a_list"),
            ({"foo": None}, "null"),
        ]

        for data, error_code in invalid_values:
            with self.subTest(data=data):
                is_valid, errors = validate_formio_data(component, data)

                self.assertFalse(is_valid)
                self.assertIn(component["key"], errors)
                error = extract_error(errors, component["key"])
                self.assertEqual(error.code, error_code)
