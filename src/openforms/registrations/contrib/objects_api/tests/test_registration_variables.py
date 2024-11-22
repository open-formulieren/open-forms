from django.test import TestCase

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
