from django.test import SimpleTestCase

from ..registration_variables import register


class RegistrationVariableTests(SimpleTestCase):

    def test_variables_handle_None_submission(self):
        for variable in register:
            with self.subTest(variable=variable.identifier):
                try:
                    variable.get_initial_value(submission=None)
                except Exception as exc:
                    raise self.failureException(
                        "Unexpected crash on None value"
                    ) from exc
