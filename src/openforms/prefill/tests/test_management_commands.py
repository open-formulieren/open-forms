from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
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
    def test_no_specifications_provided(self):
        with self.assertRaises(
            CommandError, msg="No URL to the OAS specifications was provided."
        ):
            call_command(
                "get_properties_from_oas",
            )

    @Mocker()
    def test_wrong_schema_provided(self, m_request_oas):
        m_request_oas.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        with self.assertRaises(
            CommandError,
            msg='The given schema name "non-existent-schema" could not be found in the specifications',
        ):
            call_command(
                "get_properties_from_oas",
                schema="non-existent-schema",
                url="https://personen/api/schema/openapi.yaml?v=3",
            )

    @Mocker()
    def test_no_schema_provided(self, m_request_oas):
        m_request_oas.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        with self.assertRaises(
            CommandError,
            msg="No schema specified",
        ):
            call_command(
                "get_properties_from_oas",
                url="https://personen/api/schema/openapi.yaml?v=3",
            )

    @Mocker()
    def test_happy_flow(self, m_request_oas):
        m_request_oas.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        stdout = StringIO()

        call_command(
            "get_properties_from_oas",
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
    command:  get_properties_from_oas --url https://personen/api/schema/openapi.yaml?v=3 --schema Datum
    \"\"\"

    dag = "dag", _("Dag")
    datum = "datum", _("Datum")
    jaar = "jaar", _("Jaar")
    maand = "maand", _("Maand")
"""

        self.assertEqual(expected_output.strip(), output.strip())

    @Mocker()
    def test_happy_flow_nested_properties(self, m_request_oas):
        m_request_oas.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        stdout = StringIO()

        call_command(
            "get_properties_from_oas",
            schema="NaamInOnderzoek",
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
    schema: NaamInOnderzoek
    command:  get_properties_from_oas --url https://personen/api/schema/openapi.yaml?v=3 --schema NaamInOnderzoek
    \"\"\"

    geslachtsnaam = "geslachtsnaam", _("Geslachtsnaam")
    voornamen = "voornamen", _("Voornamen")
    voorvoegsel = "voorvoegsel", _("Voorvoegsel")
    datumingangonderzoek_dag = "datumIngangOnderzoek.dag", _("Datumingangonderzoek > Dag")
    datumingangonderzoek_datum = "datumIngangOnderzoek.datum", _("Datumingangonderzoek > Datum")
    datumingangonderzoek_jaar = "datumIngangOnderzoek.jaar", _("Datumingangonderzoek > Jaar")
    datumingangonderzoek_maand = "datumIngangOnderzoek.maand", _("Datumingangonderzoek > Maand")
"""

        self.assertEqual(expected_output.strip(), output.strip())
