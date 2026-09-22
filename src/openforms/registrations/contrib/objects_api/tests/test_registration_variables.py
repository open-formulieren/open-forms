from django.test import TestCase

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

        variable = register["registrator"].get_initial_value(submission=submission)

        self.assertIsNone(variable)

    def test_registrator_variable_with_registrator(self):
        submission = SubmissionFactory.create()
        RegistratorInfoFactory.create(
            submission=submission,
            plugin="org-oidc",
            attribute=AuthAttribute.employee_id,
            value="some-employee@example.com",
        )

        variable = register["registrator"].get_initial_value(submission=submission)

        self.assertIsNotNone(variable)
        self.assertEqual(
            variable,
            {
                "plugin": "org-oidc",
                "attribute": "employee_id",
                "value": "some-employee@example.com",
            },
        )
