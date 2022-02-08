from django.test import SimpleTestCase

from openforms.conf.utils import Filesize

file_size = Filesize()


class FilesizeCastTests(SimpleTestCase):
    def test_nginx_measurement_units(self):
        values = (
            ("10B", 10),
            ("10b", 10),
            # nginx suffixes -> kibi/mebi
            ("10M", 10_485_760),
            ("10m", 10_485_760),
            ("50k", 51_200),
            ("50K", 51_200),
            ("1G", 1_073_741_824),
            ("1g", 1_073_741_824),
            # SI system + binary variants
            ("1MiB", 1_048_576),
            ("1MiB", 1_048_576),
            ("1KB", 1_000),
            ("1MB", 1_000_000),
            ("1GB", 1_000_000_000),
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

    def test_binary_system(self):
        file_size = Filesize(system=Filesize.S_BINARY)
        values = (
            ("10B", 10),
            ("10b", 10),
            ("50kb", 51_200),
            ("50KB", 51_200),
            ("10MB", 10_485_760),
            ("10mb", 10_485_760),
            ("1GB", 1_073_741_824),
            ("1gb", 1_073_741_824),
        )
        for value, expected in values:
            with self.subTest(input=value, expected=expected):
                result = file_size(value)

                self.assertEqual(result, expected)
