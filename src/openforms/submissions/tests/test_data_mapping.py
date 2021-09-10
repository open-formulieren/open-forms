from django.test import TestCase

from djchoices import ChoiceItem, DjangoChoices
from privates.test import temp_private_root

from openforms.registrations.constants import REGISTRATION_ATTRIBUTE
from openforms.submissions.mapping import (
    FieldConf,
    apply_data_mapping,
    get_unmapped_data,
)
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


@temp_private_root()
class MappingTests(TestCase):
    def test_kitchensink(self):
        """
        all-in-one testcase for demonstration purposes
        """
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
            "form.name": FieldConf(form_field="public_name"),
        }

        expected = {
            "initiator": {
                "naam": {
                    "voornaam": "Foo",
                    "achternaam": "Bar",
                    "tussenvoegsel": "",
                },
                "geslacht": "V",
            },
            "bsn": "111222333",
            "form": {"name": "Foo Form"},
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
            submitted_data={
                "voornamen": "Foo",
                "geslachtsnaam": "Bar",
                "geslacht": "v",
            },
            form__public_name="Foo Form",
            bsn="111222333",
        )

        actual = apply_data_mapping(
            submission, mapping, component_attribute=REGISTRATION_ATTRIBUTE
        )
        self.assertEqual(actual, expected)

    def test_simple(self):
        mapping = {
            "persoon.voornaam": "xyz_voornaam",
            "persoon.achternaam": "xyz_achternaam",
        }
        submission = SubmissionFactory.from_components(
            [
                {"key": "voornaam", "mapping_attr": "xyz_voornaam"},
                {"key": "achternaam", "mapping_attr": "xyz_achternaam"},
            ],
            submitted_data={"voornaam": "Foo", "achternaam": "Bar"},
        )
        actual = apply_data_mapping(submission, mapping, "mapping_attr")
        expected = {
            "persoon": {
                "voornaam": "Foo",
                "achternaam": "Bar",
            },
        }
        self.assertEqual(actual, expected)

    def test_skip_missing(self):
        mapping = {
            "persoon.voornaam": "xyz_voornaam",
            "persoon.achternaam": "xyz_achternaam",
        }
        submission = SubmissionFactory.from_components(
            [
                {"key": "voornaam", "mapping_attr": "xyz_voornaam"},
                {"key": "achternaam", "mapping_attr": "xyz_achternaam"},
            ],
            # we only submit part of the data
            submitted_data={"voornaam": "Foo"},
        )
        actual = apply_data_mapping(submission, mapping, "mapping_attr")
        expected = {
            "persoon": {
                "voornaam": "Foo",
                # missing data is skipped
            },
        }
        self.assertEqual(actual, expected)

    def test_use_conf(self):
        mapping = {
            "persoon.voornaam": FieldConf("xyz_voornaam"),
        }
        submission = SubmissionFactory.from_components(
            [
                {"key": "voornaam", "mapping_attr": "xyz_voornaam"},
            ],
            submitted_data={"voornaam": "Foo"},
        )
        actual = apply_data_mapping(submission, mapping, "mapping_attr")
        expected = {
            "persoon": {
                "voornaam": "Foo",
            },
        }
        self.assertEqual(actual, expected)

    def test_use_conf_default(self):
        mapping = {
            "persoon.voornaam": FieldConf("xyz_voornaam", default="Bar"),
        }
        submission = SubmissionFactory.from_components(
            [
                {"key": "voornaam", "mapping_attr": "xyz_voornaam"},
            ],
            submitted_data=None,
        )
        actual = apply_data_mapping(submission, mapping, "mapping_attr")
        expected = {
            "persoon": {
                "voornaam": "Bar",
            },
        }
        self.assertEqual(actual, expected)

    def test_use_conf_transform(self):
        mapping = {
            "persoon.voornaam": FieldConf(
                "xyz_voornaam", transform=lambda v: v.upper()
            ),
        }
        submission = SubmissionFactory.from_components(
            [
                {"key": "voornaam", "mapping_attr": "xyz_voornaam"},
            ],
            submitted_data={"voornaam": "Foo"},
        )
        actual = apply_data_mapping(submission, mapping, "mapping_attr")
        expected = {
            "persoon": {
                "voornaam": "FOO",
            },
        }
        self.assertEqual(actual, expected)

    def test_use_model_kwargs(self):
        mapping = {
            "persoon.voornaam": "xyz_voornaam",
            "form": FieldConf(form_field="public_name"),
            "bsn": FieldConf(submission_field="bsn"),
        }
        submission = SubmissionFactory.from_components(
            [
                {"key": "voornaam", "mapping_attr": "xyz_voornaam"},
            ],
            submitted_data={"voornaam": "Foo"},
            form__public_name="BarForm",
            bsn="111222333",
        )
        actual = apply_data_mapping(submission, mapping, "mapping_attr")
        expected = {
            "bsn": "111222333",
            "form": "BarForm",
            "persoon": {
                "voornaam": "Foo",
            },
        }
        self.assertEqual(actual, expected)

    def test_get_unmapped_data(self):
        mapping = {
            "persoon.voornaam": "xyz_voornaam",
        }
        submission = SubmissionFactory.from_components(
            [
                {"key": "voornaam", "mapping_attr": "xyz_voornaam"},
                {"key": "bijnaam"},
            ],
            submitted_data={"voornaam": "Foo", "bijnaam": "Bar"},
        )
        actual = get_unmapped_data(submission, mapping, "mapping_attr")
        expected = {
            "bijnaam": "Bar",
        }
        self.assertEqual(actual, expected)
