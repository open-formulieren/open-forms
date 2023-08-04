from textwrap import dedent

from django.test import SimpleTestCase

from requests_mock import Mocker

from ..attributes_generator import (
    AttributeGeneratorException,
    OpenApi3AttributesGenerator,
)
from .utils import load_binary_mock


class TestOpenApi3AttributesGenerator(SimpleTestCase):
    def test_no_specifications_provided(self):
        generator = OpenApi3AttributesGenerator()

        with self.assertRaises(
            AttributeGeneratorException,
            msg="No OAS specification URI was provided.",
        ):
            generator.generate_attributes()

    @Mocker()
    def test_wrong_schema_provided(self, m_request_oas):
        m_request_oas.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        generator = OpenApi3AttributesGenerator(
            schema="non-existent-schema",
            uri="https://personen/api/schema/openapi.yaml?v=3",
        )

        with self.assertRaises(
            AttributeGeneratorException,
            msg='The given schema name "non-existent-schema" could not be found in the specifications',
        ):
            generator.generate_attributes()

    @Mocker()
    def test_no_schema_provided(self, m_request_oas):
        m_request_oas.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        generator = OpenApi3AttributesGenerator(
            uri="https://personen/api/schema/openapi.yaml?v=3",
        )

        with self.assertRaises(
            AttributeGeneratorException,
            msg="No schema specified",
        ):
            generator.generate_attributes()

    @Mocker()
    def test_happy_flow(self, m_request_oas):
        m_request_oas.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        generator = OpenApi3AttributesGenerator(
            schema="Datum",
            uri="https://personen/api/schema/openapi.yaml?v=3",
            command="test",
        )

        output = generator.generate_attributes()

        expected_output = dedent(
            """
            from django.db import models
            from django.utils.translation import gettext_lazy as _

            class Attributes(models.TextChoices):
                \"\"\"
                This code was (at some point) generated from the management command below. Names and labels are in Dutch if the spec was Dutch
                specs: https://personen/api/schema/openapi.yaml?v=3
                schema: Datum
                command: test
                \"\"\"

                dag = "dag", _("Dag")
                datum = "datum", _("Datum")
                jaar = "jaar", _("Jaar")
                maand = "maand", _("Maand")
            """
        )

        self.assertEqual(expected_output.strip(), output.strip())

    @Mocker()
    def test_happy_flow_nested_properties(self, m_request_oas):
        m_request_oas.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("personen.yaml"),
        )
        generator = OpenApi3AttributesGenerator(
            schema="NaamInOnderzoek",
            uri="https://personen/api/schema/openapi.yaml?v=3",
            command="test",
        )

        output = generator.generate_attributes()

        expected_output = dedent(
            """
            from django.db import models
            from django.utils.translation import gettext_lazy as _

            class Attributes(models.TextChoices):
                \"\"\"
                This code was (at some point) generated from the management command below. Names and labels are in Dutch if the spec was Dutch
                specs: https://personen/api/schema/openapi.yaml?v=3
                schema: NaamInOnderzoek
                command: test
                \"\"\"

                geslachtsnaam = "geslachtsnaam", _("Geslachtsnaam")
                voornamen = "voornamen", _("Voornamen")
                voorvoegsel = "voorvoegsel", _("Voorvoegsel")
                datumingangonderzoek_dag = "datumIngangOnderzoek.dag", _("Datumingangonderzoek > Dag")
                datumingangonderzoek_datum = "datumIngangOnderzoek.datum", _("Datumingangonderzoek > Datum")
                datumingangonderzoek_jaar = "datumIngangOnderzoek.jaar", _("Datumingangonderzoek > Jaar")
                datumingangonderzoek_maand = "datumIngangOnderzoek.maand", _("Datumingangonderzoek > Maand")
            """
        )

        self.assertEqual(expected_output.strip(), output.strip())
