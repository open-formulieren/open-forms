from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from requests_mock import Mocker

from ..contrib.demo.plugin import DemoPrefill
from ..contrib.haalcentraal.tests.utils import load_binary_mock
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


class TestGetPropertiesFromOAS(SimpleTestCase):
    @Mocker()
    def test_generate_attributes_openapi3_parser(self, m_request_oas):
        m_request_oas.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        stdout = StringIO()

        call_command(
            "generate_prefill_from_spec",
            parser="openapi3-parser",
            schema="Datum",
            url="https://personen/api/schema/openapi.yaml?v=3",
            stdout=stdout,
        )

        stdout.seek(0)
        output = stdout.read()

        expected_output = """
from django.db import models
from django.utils.translation import gettext_lazy as _

class Attributes(models.TextChoices):
    \"\"\"
    This code was (at some point) generated from the management command below. Names and labels are in Dutch if the spec was Dutch
    specs: https://personen/api/schema/openapi.yaml?v=3
    schema: Datum
    command: manage.py generate_prefill_from_spec --parser openapi3-parser --url https://personen/api/schema/openapi.yaml?v=3 --schema Datum
    \"\"\"

    dag = "dag", _("Dag")
    datum = "datum", _("Datum")
    jaar = "jaar", _("Jaar")
    maand = "maand", _("Maand")
"""

        self.assertEqual(expected_output.strip(), output.strip())
