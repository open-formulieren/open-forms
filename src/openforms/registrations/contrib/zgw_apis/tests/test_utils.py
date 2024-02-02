from django.test import SimpleTestCase

from ..utils import process_according_to_eigenschap_format


class UtilsTests(SimpleTestCase):
    def test_valid_date_is_successfully_processed(self):
        specificatie = {
            "groep": "",
            "formaat": "datum",
            "lengte": "14",
            "kardinaliteit": "1",
            "waardenverzameling": [],
        }
        sample = "2024-11-09"
        processed_value = process_according_to_eigenschap_format(specificatie, sample)

        self.assertEqual(processed_value, "20241109")

    def test_valid_datetime_is_successfully_processed(self):
        specificatie = {
            "groep": "",
            "formaat": "datum_tijd",
            "lengte": "14",
            "kardinaliteit": "1",
            "waardenverzameling": [],
        }
        sample = "2024-01-31T16:24:00+00:00"
        processed_value = process_according_to_eigenschap_format(specificatie, sample)

        self.assertEqual(processed_value, "20240131172400")

    def test_no_date_or_datetime(self):
        samples = ["simple string", "2"]
        specificatie = {
            "groep": "",
            "formaat": "tekst",
            "lengte": "14",
            "kardinaliteit": "1",
            "waardenverzameling": [],
        }

        for s in samples:
            processed_value = process_according_to_eigenschap_format(specificatie, s)
            self.assertEqual(processed_value, s)

    def test_invalid_date_raises_value_error(self):
        specificatie = {
            "groep": "",
            "formaat": "datum",
            "lengte": "14",
            "kardinaliteit": "1",
            "waardenverzameling": [],
        }
        sample = "2024-11-091"

        with self.assertRaisesMessage(
            ValueError, f"Invalid isoformat string: '{sample}'"
        ):
            process_according_to_eigenschap_format(specificatie, sample)

    def test_invalid_datetime_raises_value_error(self):
        specificatie = {
            "groep": "",
            "formaat": "datum_tijd",
            "lengte": "14",
            "kardinaliteit": "1",
            "waardenverzameling": [],
        }
        sample = "2024-01-313T12:07:00+01:00"

        with self.assertRaisesMessage(
            ValueError, f"Invalid isoformat string: '{sample}'"
        ):
            process_according_to_eigenschap_format(specificatie, sample)
