from django.test import TestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.factories import RegistratorInfoFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..registration_variables import register


class RegistrationVariableTests(TestCase):
    def test_variables_handle_None_submission(self):
        for variable in register:
            with self.subTest(variable=variable.identifier):
                try:
                    variable.get_initial_value(submission=None)
                except Exception as exc:
                    raise self.failureException(
                        "Unexpected crash on None value"
                    ) from exc

    def test_registrator_variable_without_registrator(self):
        submission = SubmissionFactory.create()
        assert submission.has_registrator is False

        value = register["registrator"].get_initial_value(submission=submission)

        self.assertIsNone(value)

    def test_registrator_variable_with_registrator_but_no_oidc_claims(self):
        user = UserFactory.create(is_staff=True, raw_oidc_claims={}, employee_id="9999")
        submission = SubmissionFactory.create()
        RegistratorInfoFactory.create(
            submission=submission,
            plugin="org-oidc",
            attribute=AuthAttribute.local_user_id,
            value=str(user.pk),
        )

        value = register["registrator"].get_initial_value(submission=submission)

        self.assertIsNotNone(value)
        self.assertEqual(
            value,
            {
                "plugin": "org-oidc",
                "attribute": "employee_id",
                "value": "9999",
                "oidc_claims": None,
            },
        )

    def test_registrator_variable_with_registrator_and_oidc_claims(self):
        user = UserFactory.create(
            is_staff=True,
            employee_id="9999",
            raw_oidc_claims={
                "aud": "testid",
                "email": "admin@example.com",
                "email_verified": True,
                "employeeId": "9999",
                "groups": [
                    "Registreerders",
                    "default-roles-test",
                    "offline_access",
                    "uma_authorization",
                ],
                "iss": "http://localhost:8080/realms/test",
                "preferred_username": "admin",
                "sub": "6db2db87-de31-4e30-9f25-cefe5da8b154",
            },
        )
        submission = SubmissionFactory.create()
        RegistratorInfoFactory.create(
            submission=submission,
            plugin="org-oidc",
            attribute=AuthAttribute.local_user_id,
            value=str(user.pk),
        )

        value = register["registrator"].get_initial_value(submission=submission)

        self.assertIsNotNone(value)
        self.assertEqual(
            value,
            {
                "plugin": "org-oidc",
                "attribute": "employee_id",
                "value": "9999",
                "oidc_claims": {
                    "aud": "testid",
                    "email": "admin@example.com",
                    "email_verified": True,
                    "employeeId": "9999",
                    "groups": [
                        "Registreerders",
                        "default-roles-test",
                        "offline_access",
                        "uma_authorization",
                    ],
                    "iss": "http://localhost:8080/realms/test",
                    "preferred_username": "admin",
                    "sub": "6db2db87-de31-4e30-9f25-cefe5da8b154",
                },
            },
        )
