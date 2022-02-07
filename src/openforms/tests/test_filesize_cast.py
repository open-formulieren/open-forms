from django.test import SimpleTestCase

from openforms.conf.utils import Filesize

file_size = Filesize()


class FilesizeCastTests(SimpleTestCase):
    def test_nginx_measurement_units(self):
        values = (
            # nginx suffixes -> kibi/mebi
            ("10M", 10_485_760),
            ("10m", 10_485_760),
            ("50k", 51_200),
            ("50K", 51_200),
            # SI system + binary variants
            ("1MiB", 1_048_576),
            ("1MiB", 1_048_576),
            ("1KB", 1_000),
            ("1MB", 1_000_000),
        )
        for value, expected in values:
            with self.subTest(input=value, expected=expected):
                result = file_size(value)

                self.assertEqual(result, expected)

    def test_int(self):
        value = file_size(1024)

        self.assertEqual(value, 1024)

    def test_str_without_suffix(self):
        value = file_size("1000")

        self.assertEqual(value, 1_000)

    def test_no_whitespace_allowed(self):
        with self.assertRaises(ValueError):
            file_size("10 MB")

    def test_invalid_pattern(self):
        with self.assertRaises(ValueError):
            file_size("10MB9")

    def test_unsupported_unit(self):
        with self.assertRaises(ValueError):
            file_size("10Zorgs")
