from django.test import TestCase

from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ...form_logic import evaluate_form_logic
from ..factories import SubmissionFactory, SubmissionStepFactory


class DeterministicEvaluationTests(TestCase):
    def test_logic_rule_order_respected(self):
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form, form_definition__configuration={"components": []}
        )
        FormVariableFactory.create(
            form=form,
            key="a",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.int,
        )
        FormLogicFactory.create(
            form=form,
            order=1,
            json_logic_trigger={"==": [1, 1]},
            actions=[
                {
                    "variable": "a",
                    "action": {
                        "name": "Add 2",
                        "type": "variable",
                        "value": {"+": [{"var": "a"}, 2]},
                    },
                }
            ],
        )
        FormLogicFactory.create(
            form=form,
            order=0,
            json_logic_trigger={"==": [1, 1]},
            actions=[
                {
                    "variable": "a",
                    "action": {
                        "name": "Multiply by 2",
                        "type": "variable",
                        "value": {"*": [{"var": "a"}, 2]},
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission, form_step=step, data={"a": 3}
        )

        evaluate_form_logic(submission, submission_step)

        state = submission.load_submission_value_variables_state()
        variable = state.variables["a"]
        self.assertEqual(variable.value, 8)  # ( 3 x 2 ) + 2

    def test_evaluate_rules_when_trigger_step_reached(self):
        """
        Test that only the rules are evaluated that reached the trigger step.

        Set up creates a form with three steps, the logic rule may only kick in from
        step2 onwards (i.e. - evaluate for step 2 and for step 3, but not step 1).
        """
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "a",
                    },
                    {
                        "type": "number",
                        "key": "b",
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "c",
                    }
                ]
            },
        )
        step3 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "d",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [1, 1]},  # trigger is always true
            trigger_from_step=step2,
            actions=[
                {
                    "variable": "d",
                    "action": {
                        "name": "Add a and b",
                        "type": "variable",
                        "value": {"+": [{"var": "a"}, {"var": "b"}]},
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        ss1 = SubmissionStepFactory.create(
            submission=submission, form_step=step1, data={"a": 2, "b": 4}
        )

        # tests and assertions, check for every step that the evaluation is/isn't performed

        with self.subTest("Evaluation skipped on step 1"):
            evaluate_form_logic(submission, ss1)

            state = submission.load_submission_value_variables_state()
            var_a = state.variables["a"]
            var_b = state.variables["b"]
            self.assertEqual(var_a.value, 2)
            self.assertEqual(var_b.value, 4)

        with self.subTest("Evaluation not skipped on step 2"):
            ss2 = SubmissionStepFactory.create(
                submission=submission, form_step=step2, data={"c": 2}
            )

            evaluate_form_logic(submission, ss2)

            state = submission.load_submission_value_variables_state()
            var_c = state.variables["c"]
            var_d = state.variables["d"]
            self.assertEqual(var_c.value, 2)
            self.assertEqual(var_d.value, 6)

        with self.subTest("Evaluation not skipped on step 3"):
            ss3 = SubmissionStepFactory.create(
                submission=submission, form_step=step3, data={"d": 1}
            )

            evaluate_form_logic(submission, ss3)

            state = submission.load_submission_value_variables_state()
            self.assertEqual(ss3.data, {"d": 6})
