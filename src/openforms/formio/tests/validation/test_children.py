from django.test import TestCase

from openforms.forms.tests.factories import FormVariableFactory
from openforms.prefill.contrib.family_members.plugin import PLUGIN_IDENTIFIER
from openforms.submissions.tests.factories import SubmissionFactory

from ...typing.custom import ChildrenComponent
from .helpers import extract_error, validate_formio_data


class ChildrenValidationTests(TestCase):
    def test_valid_data(self):
        component: ChildrenComponent = {
            "type": "children",
            "key": "children",
            "label": "Children",
            "enableSelection": False,
        }

        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_children",
            data_type="array",
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "initials": "P.",
                    "affixes": "van",
                    "lastName": "Paassen",
                    "dateOfBirth": "2016-02-01",
                    "deceased": False,
                }
            ],
        )

        valid_values = {
            "children": [
                {
                    "bsn": "999970409",
                    "firstNames": "Pero",
                    "dateOfBirth": "2016-02-01",
                    "selected": None,
                }
            ]
        }

        is_valid, _ = validate_formio_data(component, valid_values, submission)

        self.assertTrue(is_valid)

    def test_invalid_data(self):
        component: ChildrenComponent = {
            "key": "children",
            "type": "children",
            "label": "children invalid data",
            "enableSelection": False,
        }

        invalid_values = {
            "children": [
                {
                    "bsn": "223",
                    "firstNames": "Pero",
                    "dateOfBirth": "2016-02-01",
                }
            ]
        }

        is_valid, errors = validate_formio_data(component, invalid_values)

        bsn_error = extract_error(errors["children"][0], "bsn")

        self.assertFalse(is_valid)
        self.assertEqual(bsn_error.code, "invalid")

    def test_missing_keys(self):
        component: ChildrenComponent = {
            "key": "children",
            "type": "children",
            "label": "children missing keys",
            "enableSelection": False,
        }

        missing_keys = {
            "children": [
                {
                    "firstNames": "Pero",
                    "dateOfBirth": "01-01",
                }
            ]
        }

        is_valid, errors = validate_formio_data(component, missing_keys)

        bsn_error = extract_error(errors["children"][0], "bsn")
        selected_error = extract_error(errors["children"][0], "bsn")

        self.assertFalse(is_valid)
        self.assertEqual(bsn_error.code, "required")
        self.assertEqual(selected_error.code, "required")

    def test_valid_data_for_selected_field(self):
        component: ChildrenComponent = {
            "type": "children",
            "key": "children",
            "label": "Children",
            "enableSelection": True,
        }

        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_children",
            data_type="array",
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "",
                    "initials": "P.",
                    "affixes": "van",
                    "lastName": "Paassen",
                    "dateOfBirth": "2020-01-01",
                    "deceased": False,
                }
            ],
        )

        valid_data = {
            "children": [
                {
                    "bsn": "999970409",
                    "firstNames": "",
                    "dateOfBirth": "2020-01-01",
                    "selected": True,
                }
            ]
        }

        is_valid, _ = validate_formio_data(component, valid_data, submission)

        self.assertTrue(is_valid)

    def test_invalid_data_for_selected_field(self):
        component: ChildrenComponent = {
            "type": "children",
            "key": "children",
            "label": "Children",
            "enableSelection": False,
        }

        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        FormVariableFactory.create(
            form=submission.form,
            user_defined=True,
            key="immutable_children",
            data_type="array",
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
            },
            initial_value=[
                {
                    "bsn": "999970409",
                    "firstNames": "",
                    "initials": "P.",
                    "affixes": "van",
                    "lastName": "Paassen",
                    "dateOfBirth": "2020-01-01",
                    "deceased": False,
                },
            ],
        )

        invalid_data = {
            "children": [
                {
                    "bsn": "999970409",
                    "firstNames": "",
                    "dateOfBirth": "2020-01-01",
                    "selected": True,
                }
            ]
        }

        is_valid, errors = validate_formio_data(component, invalid_data, submission)

        selected_error = extract_error(errors, "children")

        self.assertFalse(is_valid)
        self.assertEqual(selected_error.code, "invalid")
