from datetime import datetime

from django.test import SimpleTestCase

from openforms.submissions.tests.factories import SubmissionFactory

from ..registration_variables import register


class VariableEvaluationTests(SimpleTestCase):
    def test_no_crash_when_no_submission_given(self):
        for name in (
            "payment_completed",
            "payment_amount",
            "payment_public_order_ids",
            "provider_payment_ids",
            "completed_on",
        ):
            with self.subTest(variable=name):
                variable = register[name]

                try:
                    variable.get_static_variable(submission=None)
                except Exception as exc:
                    raise self.failureException(
                        "Variable must be able to handle None"
                    ) from exc

    def test_submission_completed_on_returns_datetime(self):
        submission = SubmissionFactory.build(completed=True)
        variable = register["completed_on"]

        variable = variable.get_static_variable(submission=submission)

        assert isinstance(variable.initial_value, datetime)
        self.assertIsNotNone(variable.initial_value.tzinfo)
