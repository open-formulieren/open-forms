from django.test import TestCase

from openforms.forms.tests.factories import FormVariableFactory
from openforms.prefill.contrib.family_members.plugin import PLUGIN_IDENTIFIER
from openforms.submissions.tests.factories import SubmissionFactory

from ...typing.custom import Component
from .helpers import extract_error, validate_formio_data


class PartnersValidationTests(TestCase):
    def test_valid_data(self):
        component: Component = {
            "type": "partners",
            "key": "partners",
            "label": "Partners",
        }

        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_partners",
            data_type="array",
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "initials": "P.",
                    "affixes": "van",
                    "lastName": "Paassen",
                    "firstNames": "Pero",
                    "dateOfBirth": "2023-02-01",
                    "deceased": None,
                }
            ],
        )

        valid_values = {
            "partners": [
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "initials": "P.",
                    "affixes": "van",
                    "lastName": "Paassen",
                    "dateOfBirth": "2023-02-01",
                    "selected": None,
                }
            ]
        }

        is_valid, _ = validate_formio_data(component, valid_values, submission)

        self.assertTrue(is_valid)

    def test_invalid_data(self):
        component: Component = {
            "key": "partners",
            "type": "partners",
            "label": "Partners invalid data",
        }

        invalid_values = {
            "partners": [
                {
                    "bsn": "223",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "firstNames": "",
                    "dateOfBirth": "01-01",
                    "deceased": None,
                }
            ]
        }

        is_valid, errors = validate_formio_data(component, invalid_values)

        bsn_error = extract_error(errors["partners"][0], "bsn")

        self.assertFalse(is_valid)
        self.assertEqual(bsn_error.code, "invalid")

    def test_missing_keys(self):
        component: Component = {
            "key": "partners",
            "type": "partners",
            "label": "Partners missing keys",
        }

        invalid_keys = {
            "partners": [
                {
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "firstNames": "",
                    "dateOfBirth": "01-01",
                    "deceased": None,
                }
            ]
        }

        is_valid, errors = validate_formio_data(component, invalid_keys)

        bsn_error = extract_error(errors["partners"][0], "bsn")

        self.assertFalse(is_valid)
        self.assertEqual(bsn_error.code, "required")
