from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from ..contrib.demo.plugin import DemoPrefill
from ..registry import Registry

# set up an isolated registry
register = Registry()
register("test")(DemoPrefill)


@override_settings(LANGUAGE_CODE="en")
@patch(
    "openforms.prefill.management.commands.list_prefill_plugins.register", new=register
)
class ListPluginsTests(SimpleTestCase):
    def test_list_plugins(self, *mocks):
        stdout = StringIO()
        stderr = StringIO()

        call_command(
            "list_prefill_plugins", stdout=stdout, stderr=stderr, no_color=True
        )

        stdout.seek(0)
        stderr.seek(0)

        self.assertEqual(stderr.read(), "")

        output = stdout.read()

        expected = """Available plugins:
  test (Demo)
  * random_number (Random number)
  * random_string (Random string)
"""
        self.assertEqual(output, expected)
