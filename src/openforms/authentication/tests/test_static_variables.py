from uuid import UUID

from django.test import TestCase

from jsonschema.validators import Draft202012Validator

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import AuthInfoFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.variables.service import get_static_variables

from ..static_variables.static_variables import register_static_variable as registry


def _get_json_schema(key: str):
    return registry[key].as_json_schema()


class TestStaticVariables(TestCase):
    def test_auth_static_data(self):
        auth_info = AuthInfoFactory.create(
            plugin="test-plugin",
            attribute=AuthAttribute.bsn,
            value="111222333",
            additional_claims={
                "firstName": "John",
                "familyName": "Doe",
            },
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
                "additional_claims": {
                    "firstName": "John",
                    "familyName": "Doe",
                },
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

    def test_branch_number_variable(self):
        cases = (
            (
                AuthInfoFactory.create(
                    is_digid=True,
                    legal_subject_service_restriction="foo",
                ),
                "",
            ),
            (
                AuthInfoFactory.create(
                    is_digid_machtigen=True,
                    legal_subject_service_restriction="foo",
                ),
                "",
            ),
            (
                AuthInfoFactory.create(
                    is_eh=True,
                    legal_subject_service_restriction="123456789012",
                ),
                "123456789012",
            ),
            (
                AuthInfoFactory.create(
                    is_eh_bewindvoering=True,
                    legal_subject_service_restriction="123456789012",
                ),
                "123456789012",
            ),
            (
                AuthInfoFactory.create(
                    is_eh=True,
                    legal_subject_service_restriction="",
                ),
                "",
            ),
            (
                AuthInfoFactory.create(
                    is_eh_bewindvoering=True,
                    legal_subject_service_restriction="",
                ),
                "",
            ),
        )
        for auth_info, expected in cases:
            with self.subTest(
                attribute=auth_info.attribute,
                service_restriction=auth_info.legal_subject_service_restriction,
            ):
                static_data = {
                    variable.key: variable.initial_value
                    for variable in get_static_variables(
                        submission=auth_info.submission
                    )
                }

                self.assertEqual(static_data["auth_context_branch_number"], expected)

    def test_additional_claims_variable(self):
        auth_info = AuthInfoFactory.create(
            plugin="test-plugin",
            attribute=AuthAttribute.bsn,
            value="111222333",
            additional_claims={
                "firstName": "John",
                "familyName": "Doe",
            },
        )

        static_data = {
            variable.key: variable.initial_value
            for variable in get_static_variables(submission=auth_info.submission)
        }

        self.assertEqual(
            static_data["auth_additional_claims"],
            {"firstName": "John", "familyName": "Doe"},
        )

    def test_static_variables_in_confirmation_email(self):
        auth_info = AuthInfoFactory.create(
            plugin="test-plugin",
            attribute=AuthAttribute.bsn,
            value="111222333",
            additional_claims={
                "firstName": "John",
                "familyName": "Doe",
            },
        )

        excluded_variables = [
            "auth",
            "auth_bsn",
            "auth_kvk",
            "auth_pseudo",
            "auth_additional_claims",
            "auth_context_loa",
            "auth_context_representee_identifier_type",
            "auth_context_representee_identifier",
            "auth_context_legal_subject_identifier_type",
            "auth_context_legal_subject_identifier",
            "auth_context_branch_number",
            "auth_context_acting_subject_identifier_type",
            "auth_context_acting_subject_identifier",
        ]
        included_variables = [
            "submission_id",
            "language_code",
            "auth_type",
            "auth_context_source",
        ]

        static_data = {
            variable.key: variable
            for variable in get_static_variables(
                submission=auth_info.submission, is_confirmation_email=True
            )
        }

        for variable in excluded_variables:
            with self.subTest(variable):
                self.assertNotIn(variable, static_data)

        for variable in included_variables:
            with self.subTest(variable):
                self.assertIn(variable, static_data)


class StaticVariableValidJsonSchemaTests(TestCase):
    validator = Draft202012Validator

    def assertValidSchema(self, properties):
        schema = {
            "$schema": self.validator.META_SCHEMA["$id"],
            **properties,
        }

        self.assertIn("type", schema)
        self.validator.check_schema(schema)

    def test_submission_id(self):
        schema = _get_json_schema("submission_id")
        self.assertValidSchema(schema)

    def test_language_code(self):
        schema = _get_json_schema("language_code")
        self.assertValidSchema(schema)

    def test_auth(self):
        schema = _get_json_schema("auth")
        self.assertValidSchema(schema)

    def test_auth_type(self):
        schema = _get_json_schema("auth_type")
        self.assertValidSchema(schema)

    def test_auth_bsn(self):
        schema = _get_json_schema("auth_bsn")
        self.assertValidSchema(schema)

    def test_auth_kvk(self):
        schema = _get_json_schema("auth_kvk")
        self.assertValidSchema(schema)

    def test_auth_pseudo(self):
        schema = _get_json_schema("auth_pseudo")
        self.assertValidSchema(schema)

    def test_auth_additional_claims(self):
        schema = _get_json_schema("auth_additional_claims")
        self.assertValidSchema(schema)

    def test_auth_context(self):
        schema = _get_json_schema("auth_context")
        self.assertValidSchema(schema)

    def test_auth_context_source(self):
        schema = _get_json_schema("auth_context_source")
        self.assertValidSchema(schema)

    def test_auth_context_loa(self):
        schema = _get_json_schema("auth_context_loa")
        self.assertValidSchema(schema)

    def test_auth_context_representee_type(self):
        schema = _get_json_schema("auth_context_representee_identifier_type")
        self.assertValidSchema(schema)

    def test_auth_context_representee_identifier(self):
        schema = _get_json_schema("auth_context_representee_identifier")
        self.assertValidSchema(schema)

    def test_auth_context_legal_subject_identifier_type(self):
        schema = _get_json_schema("auth_context_legal_subject_identifier_type")
        self.assertValidSchema(schema)

    def test_auth_context_legal_subject_identifier(self):
        schema = _get_json_schema("auth_context_legal_subject_identifier")
        self.assertValidSchema(schema)

    def test_auth_context_branch_number(self):
        schema = _get_json_schema("auth_context_branch_number")
        self.assertValidSchema(schema)

    def test_auth_context_acting_subject_identifier_type(self):
        schema = _get_json_schema("auth_context_acting_subject_identifier_type")
        self.assertValidSchema(schema)

    def test_auth_context_acting_subject_identifier(self):
        schema = _get_json_schema("auth_context_acting_subject_identifier")
        self.assertValidSchema(schema)


class LanguageCodeTests(TestCase):
    def test_enum_in_json_schema(self):
        schema = _get_json_schema("language_code")
        self.assertEqual(schema["enum"], ["nl", "en"])
