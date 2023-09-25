from pathlib import Path
from textwrap import dedent

from django.conf import settings
from django.test import SimpleTestCase

from ..attributes_generator import (
    AttributeGeneratorException,
    OpenApi3AttributesGenerator,
)

OAS_URI = (
    Path(settings.DJANGO_PROJECT_DIR)
    / "contrib"
    / "haal_centraal"
    / "tests"
    / "files"
    / "personen.yaml"
).as_uri()


class TestOpenApi3AttributesGenerator(SimpleTestCase):
    def test_no_specifications_provided(self):
        generator = OpenApi3AttributesGenerator()

        with self.assertRaises(
            AttributeGeneratorException,
            msg="No OAS specification URI was provided.",
        ):
            generator.generate_attributes()

    def test_wrong_schema_provided(self):
        generator = OpenApi3AttributesGenerator(
            schema="non-existent-schema",
            uri=OAS_URI,
        )

        with self.assertRaises(
            AttributeGeneratorException,
            msg='The given schema name "non-existent-schema" could not be found in the specifications',
        ):
            generator.generate_attributes()

    def test_no_schema_provided(self):
        generator = OpenApi3AttributesGenerator(
            uri=OAS_URI,
        )

        with self.assertRaises(
            AttributeGeneratorException,
            msg="No schema specified",
        ):
            generator.generate_attributes()

    def test_happy_flow(self):
        generator = OpenApi3AttributesGenerator(
            schema="Datum",
            uri=OAS_URI,
            command="test",
        )

        output = generator.generate_attributes()

        expected_output = dedent(
            f"""
            from django.db import models
            from django.utils.translation import gettext_lazy as _

            class Attributes(models.TextChoices):
                \"\"\"
                This code was (at some point) generated from the management command below. Names and labels are in Dutch if the spec was Dutch
                spec: {OAS_URI}
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

    def test_happy_flow_nested_properties(self):
        generator = OpenApi3AttributesGenerator(
            schema="NaamInOnderzoek",
            uri=OAS_URI,
            command="test",
        )

        output = generator.generate_attributes()

        expected_output = dedent(
            f"""
            from django.db import models
            from django.utils.translation import gettext_lazy as _

            class Attributes(models.TextChoices):
                \"\"\"
                This code was (at some point) generated from the management command below. Names and labels are in Dutch if the spec was Dutch
                spec: {OAS_URI}
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
