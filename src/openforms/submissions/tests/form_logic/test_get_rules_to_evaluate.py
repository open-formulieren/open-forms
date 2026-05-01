from django.test.testcases import TestCase

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.submissions.logic.rules import get_rules_to_evaluate
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.variables.constants import FormVariableDataTypes


class GetRulesToEvaluateTests(TestCase):
    def test_get_rules_to_evaluate(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "checkbox", "key": "checkbox", "label": "Checkbox"},
                    {"type": "number", "key": "number", "label": "Number"},
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            user_defined=True,
            name="user_defined",
            key="user_defined",
            data_type=FormVariableDataTypes.string,
        )

        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "variable": "number",
                    "action": {
                        "name": "Set number",
                        "type": LogicActionTypes.variable,
                        "value": 42,
                    },
                }
            ],
        )
        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "component": "textfield",
                    "action": {
                        "name": "Hide textfield",
                        "type": LogicActionTypes.property,
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                }
            ],
        )
        rule_3 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "action": {
                        "name": "Set user_defined",
                        "type": LogicActionTypes.variable,
                        "value": "foo",
                    },
                    "variable": "user_defined",
                }
            ],
        )
        form.apply_logic_analysis()

        submission = SubmissionFactory.create(form=form)
        submission_step_1 = SubmissionStepFactory.create(
            submission=submission, form_step=step_1
        )
        submission_step_2 = SubmissionStepFactory.create(
            submission=submission, form_step=step_2
        )

        rules = get_rules_to_evaluate(submission, submission_step_1)
        self.assertEqual(list(rules), [rule_1, rule_3])

        rules = get_rules_to_evaluate(submission, submission_step_2)
        self.assertEqual(list(rules), [rule_2])

    def test_get_rules_to_evaluate_new_iterating_over_rules_does_not_exhaust_them(self):
        """
        Ensure iterating over the rules once does not exhaust them, as we iterate
        evaluation we iterate over the rules multiple times.
        """
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "checkbox", "key": "checkbox", "label": "Checkbox"},
                    {"type": "number", "key": "number", "label": "Number"},
                ]
            },
        )
        rule_1 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            actions=[
                {
                    "variable": "number",
                    "action": {
                        "name": "Set number",
                        "type": LogicActionTypes.variable,
                        "value": 42,
                    },
                }
            ],
        )
        rule_1.form_steps.set([step])
        rule_2 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "number"}, 42]},
            actions=[
                {
                    "action": {
                        "name": "Disable next step",
                        "type": LogicActionTypes.disable_next,
                        "value": 42,
                    },
                    "form_step_uuid": str(step.uuid),
                }
            ],
        )
        rule_2.form_steps.set([step])

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission, form_step=step
        )

        rules = get_rules_to_evaluate(submission, submission_step)

        for i in (0, 1):
            rule = None
            for r in rules:
                rule = r
            with self.subTest(f"Iteration {i}"):
                self.assertEqual(rule, rule_2)
