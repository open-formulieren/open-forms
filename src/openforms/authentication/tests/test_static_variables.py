from uuid import UUID

from django.test import TestCase

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import AuthInfoFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.variables.service import get_static_variables


class TestStaticVariables(TestCase):
    def test_auth_static_data(self):
        auth_info = AuthInfoFactory.create(
            plugin="test-plugin",
            attribute=AuthAttribute.bsn,
            value="111222333",
            machtigen={AuthAttribute.bsn: "123456789"},
        )

        static_data = {
            variable.key: variable
            for variable in get_static_variables(submission=auth_info.submission)
        }

        expected = {
            "auth": {
                "plugin": "test-plugin",
                "attribute": AuthAttribute.bsn,
                "value": "111222333",
                "machtigen": {AuthAttribute.bsn: "123456789"},
            },
            "auth_bsn": "111222333",
            "auth_kvk": "",
            "auth_pseudo": "",
            "auth_type": "bsn",
        }

        for variable_key, value in expected.items():
            with self.subTest(key=variable_key, value=value):
                self.assertIn(variable_key, static_data)
                self.assertEqual(static_data[variable_key].initial_value, value)

    def test_auth_static_data_no_submission(self):
        static_data = {variable.key: variable for variable in get_static_variables()}

        expected = {
            "auth": None,
            "auth_bsn": "",
            "auth_kvk": "",
            "auth_pseudo": "",
            "auth_type": "",
        }

        for variable_key, value in expected.items():
            with self.subTest(key=variable_key, value=value):
                self.assertIn(variable_key, static_data)
                self.assertEqual(static_data[variable_key].initial_value, value)

    def test_submission_id_variable(self):
        submission = SubmissionFactory.build(
            uuid=UUID("b0a84235-3afe-49ca-8f75-fc2015538b1a")
        )
        static_data = {
            variable.key: variable.initial_value
            for variable in get_static_variables(submission=submission)
        }

        self.assertEqual(
            static_data["submission_id"], "b0a84235-3afe-49ca-8f75-fc2015538b1a"
        )

    def test_language_code_variable(self):
        submission = SubmissionFactory.build(language_code="nl")
        static_data = {
            variable.key: variable.initial_value
            for variable in get_static_variables(submission=submission)
        }

        self.assertEqual(static_data["language_code"], "nl")
