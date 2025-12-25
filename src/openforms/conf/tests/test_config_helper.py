from unittest.mock import patch

from django.test import SimpleTestCase

from ..utils import config


class ConfigHelperTests(SimpleTestCase):
    def test_empty_list_as_default(self):
        value = config("SOME_TEST_ENVVAR", split=True, default=[])

        self.assertEqual(value, [])

    def test_non_empty_list_as_default(self):
        value = config("SOME_TEST_ENVVAR", split=True, default=["foo"])

        self.assertEqual(value, ["foo"])

    @patch.dict("os.environ", {"SOME_TEST_ENVVAR": "foo,bar"})
    def test_csv_envvar_to_list(self):
        value = config("SOME_TEST_ENVVAR", split=True, default=[])

        self.assertEqual(value, ["foo", "bar"])

    @patch.dict("os.environ", {"SOME_TEST_ENVVAR": "123"})
    def test_cast_to_non_str_type(self):
        value = config("SOME_TEST_ENVVAR", default=42)

        self.assertEqual(value, 123)

    def test_allow_none_default(self):
        value = config("SOME_TEST_ENVVAR", default=None)

        self.assertIsNone(value)
