from django.test import TestCase
from djchoices import ChoiceItem, DjangoChoices

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.submissions.mapping import FieldConf, apply_data_mapping
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)


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

        form = FormFactory.create(name="Foo Form")
        def1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "voornamen",
                        "type": "text",
                        "label": "voornamen",
                        "registration": {
                            "attribute": TestAttribute.initiator_voornamen,
                        },
                    },
                    {
                        "key": "geslachtsnaam",
                        "type": "text",
                        "label": "geslachtsnaam",
                        "registration": {
                            "attribute": TestAttribute.initiator_geslachtsnaam,
                        },
                    },
                ],
            }
        )
        def2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "geslacht",
                        "type": "text",
                        "label": "geslacht",
                        "registration": {
                            "attribute": "test.geslacht",
                        },
                    },
                ],
            }
        )
        step1 = FormStepFactory.create(form=form, form_definition=def1)
        step2 = FormStepFactory.create(form=form, form_definition=def2, optional=True)
        submission = SubmissionFactory.create(form=form, bsn="111222333")
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"voornamen": "Foo", "geslachtsnaam": "Bar"},
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"geslacht": "v"}
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
