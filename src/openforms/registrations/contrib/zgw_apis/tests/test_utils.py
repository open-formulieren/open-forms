from datetime import date, datetime

from django.test import SimpleTestCase

from openforms.utils.date import TIMEZONE_AMS

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
        # Submission data fetched from the state will be in native Python objects
        sample = date(2024, 11, 9)
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
        # Submission data fetched from the state will be in native Python objects with
        # timezone information
        sample = datetime(2024, 1, 31, 16, 24, 00, tzinfo=TIMEZONE_AMS)
        processed_value = process_according_to_eigenschap_format(specificatie, sample)

        self.assertEqual(processed_value, "20240131162400")

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
        # Note that an invalid datetime string will be converted to None when fetched
        # from the submission value variable state
        sample = None

        with self.assertRaisesMessage(
            ValueError, "Received value in unknown/unexpected format!"
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
        # Note that an invalid datetime string will be converted to None when fetched
        # from the submission value variable state
        sample = None

        with self.assertRaisesMessage(
            ValueError, "Received value in unknown/unexpected format!"
        ):
            process_according_to_eigenschap_format(specificatie, sample)
