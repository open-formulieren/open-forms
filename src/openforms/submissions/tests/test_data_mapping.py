from django.test import TestCase

from djchoices import ChoiceItem, DjangoChoices

from openforms.submissions.mapping import FieldConf, apply_data_mapping
from openforms.submissions.tests.factories import SubmissionFactory


class TestAttribute(DjangoChoices):
    initiator_voornamen = ChoiceItem("initiator_voornamen", "Initiator > Voornamen")
    initiator_geslachtsnaam = ChoiceItem(
        "initiator_geslachtsnaam", "Initiator > Geslachtsnaam"
    )
    initiator_tussenvoegsel = ChoiceItem(
        "initiator_tussenvoegsel", "Initiator > Tussenvoegsel"
    )
    initiator_geboortedatum = ChoiceItem(
        "initiator_geboortedatum", "Initiator > Geboortedatum"
    )


class MappingTests(TestCase):
    def test_mapping_function(self):
        mapping = {
            # nested structure with basic values in the form & submission
            "initiator.naam.voornaam": TestAttribute.initiator_voornamen,
            "initiator.naam.achternaam": TestAttribute.initiator_geslachtsnaam,
            # fields not in the form get a default value
            "initiator.naam.tussenvoegsel": FieldConf(
                TestAttribute.initiator_tussenvoegsel, default=""
            ),
            # fields not in the form and not present on the output
            "initiator.naam.geboortedatum": TestAttribute.initiator_geboortedatum,
            # submitted and transformed
            "initiator.geslacht": FieldConf(
                "test.geslacht", transform=lambda v: str(v).upper()
            ),
            # form and submission fields
            "bsn": FieldConf(submission_field="bsn"),
            "form.name": FieldConf(form_field="name"),
        }

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "voornamen",
                    "type": "text",
                    "registration": {
                        "attribute": TestAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "geslachtsnaam",
                    "type": "text",
                    "registration": {
                        "attribute": TestAttribute.initiator_geslachtsnaam,
                    },
                },
                {
                    "key": "geslacht",
                    "type": "text",
                    "registration": {
                        "attribute": "test.geslacht",
                    },
                },
            ],
            form_kwargs=dict(name="Foo Form"),
            submission_kwargs=dict(bsn="111222333"),
            submitted_data={
                "voornamen": "Foo",
                "geslachtsnaam": "Bar",
                "geslacht": "v",
            },
        )

        actual = apply_data_mapping(
            submission, mapping, component_attribute="registration.attribute"
        )

        expected = {
            "bsn": "111222333",
            "form": {"name": "Foo Form"},
            "initiator": {
                "geslacht": "V",
                "naam": {
                    "voornaam": "Foo",
                    "achternaam": "Bar",
                    "tussenvoegsel": "",
                },
            },
        }
        self.assertEqual(actual, expected)
