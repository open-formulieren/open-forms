from django.test import SimpleTestCase

from ..utils import config


class ConfigHelperTests(SimpleTestCase):
    def test_empty_list_as_default(self):
        value = config("SOME_TEST_ENVVAR", split=True, default=[])

        self.assertEqual(value, [])

    def test_non_empty_list_as_default(self):
        value = config("SOME_TEST_ENVVAR", split=True, default=["foo"])

        self.assertEqual(value, ["foo"])
