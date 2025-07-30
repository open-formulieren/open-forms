from django.test import TestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ...typing import Component
from .helpers import extract_error, validate_formio_data


class ChildrenValidationTests(TestCase):
    def test_valid_data(self):
        component: Component = {
            "key": "children",
            "type": "children",
            "label": "children missing keys",
        }

        # test the validation with only the required fields (bsn)
        valid_keys = {
            "children": [
                {
                    "bsn": "123456782",
                }
            ]
        }

        # Must create a submission and save it here because form instance needs to have
        # a primary key value before this relationship can be used in the serializer validation
        # validate_formio_data is just building the submission, not creating it.
        submission = SubmissionFactory.create()

        is_valid, _ = validate_formio_data(component, valid_keys, submission)

        self.assertTrue(is_valid)

    def test_invalid_data(self):
        component: Component = {
            "key": "children",
            "type": "children",
            "label": "children invalid data",
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
        component: Component = {
            "key": "children",
            "type": "children",
            "label": "children missing keys",
        }

        invalid_keys = {
            "children": [
                {
                    "firstNames": "Pero",
                    "dateOfBirth": "01-01",
                }
            ]
        }

        is_valid, errors = validate_formio_data(component, invalid_keys)

        bsn_error = extract_error(errors["children"][0], "bsn")

        self.assertFalse(is_valid)
        self.assertEqual(bsn_error.code, "required")
