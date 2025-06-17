from django.test import SimpleTestCase

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class PartnersValidationTests(SimpleTestCase):
    def test_invalid_data(self):
        component: Component = {
            "key": "partners",
            "type": "partners",
            "label": "Partners invalid data",
        }

        invalid_values = {
            "partners": [
                {
                    "bsn": "223",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "01-01",
                }
            ]
        }

        is_valid, errors = validate_formio_data(component, invalid_values)

        bsn_error = extract_error(errors["partners"][0], "bsn")

        self.assertFalse(is_valid)
        self.assertEqual(bsn_error.code, "invalid")

    def test_missing_keys(self):
        component: Component = {
            "key": "partners",
            "type": "partners",
            "label": "Partners missing keys",
        }

        invalid_keys = {
            "partners": [
                {
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "01-01",
                }
            ]
        }

        is_valid, errors = validate_formio_data(component, invalid_keys)

        bsn_error = extract_error(errors["partners"][0], "bsn")

        self.assertFalse(is_valid)
        self.assertEqual(bsn_error.code, "required")
