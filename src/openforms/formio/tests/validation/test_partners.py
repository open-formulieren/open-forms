from django.test import TestCase, override_settings

from openforms.forms.tests.factories import FormVariableFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.variables.constants import FormVariableDataTypes

from ...typing import Component
from .helpers import extract_error, validate_formio_data


@override_settings(LANGUAGE_CODE="en")
class PartnersValidationTests(TestCase):
    def test_valid_data(self):
        component: Component = {
            "key": "partners",
            "type": "partners",
            "label": "Partners valid data",
        }
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        valid_values = {
            "partners": [
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
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
                    "dateOfBirth": "01-01",
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
                    "dateOfBirth": "01-01",
                }
            ]
        }

        is_valid, errors = validate_formio_data(component, invalid_keys)

        bsn_error = extract_error(errors["partners"][0], "bsn")

        self.assertFalse(is_valid)
        self.assertEqual(bsn_error.code, "required")

    def test_partners_component_success_when_matched_data(self):
        component: Component = {
            "key": "partners",
            "type": "partners",
            "label": "Partners matced data",
        }
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ],
        )

        valid_data = {
            "partners": [
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                }
            ]
        }

        is_valid, errors = validate_formio_data(
            component, valid_data, submission=submission
        )

        self.assertTrue(is_valid)

    def test_partners_component_fails_when_data_is_tampered(self):
        component: Component = {
            "key": "partners",
            "type": "partners",
            "label": "Partners tampered data",
        }
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_partners",
            data_type=FormVariableDataTypes.array,
            prefill_plugin="family_members",
            prefill_options={
                "type": "partners",
                "mutable_data_form_variable": "partners",
            },
            initial_value=[
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "L",
                    "lastName": "Boei",
                    "dateOfBirth": "1990-01-01",
                },
            ],
        )

        invalid_data = {
            "partners": [
                {
                    "bsn": "123456782",
                    "initials": "",
                    "affixes": "",
                    "lastName": "Another name",
                    "dateOfBirth": "1990-01-01",
                },
            ]
        }

        is_valid, errors = validate_formio_data(
            component, invalid_data, submission=submission
        )

        error = extract_error(errors, "partners")

        self.assertFalse(is_valid)
        self.assertEqual(error.code, "invalid")
