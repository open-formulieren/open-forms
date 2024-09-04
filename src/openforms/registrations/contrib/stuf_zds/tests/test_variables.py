from django.test import SimpleTestCase

from ..registration_variables import register


class VariableEvaluationTests(SimpleTestCase):
    def test_no_crash_when_no_submission_given(self):
        for name in (
            "payment_completed",
            "payment_amount",
            "payment_public_order_ids",
            "provider_payment_ids",
        ):
            with self.subTest(variable=name):
                variable = register[name]

                try:
                    variable.get_static_variable(submission=None)
                except Exception as exc:
                    raise self.failureException(
                        "Variable must be able to handle None"
                    ) from exc
