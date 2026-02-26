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
        """
        Ensure that the logic analysis feature flag influences which rules to execute
        for each step.
        """
        form = FormFactory.create(new_logic_evaluation_enabled=False)
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
        # We set a value to the number component, so step 1 is assigned during logic rule
        # analysis.
        rule_1.form_steps.set([step_1])

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
        # We change the hidden property of the textfield component, so step 2 is
        # assigned during logic rule analysis.
        rule_2.form_steps.set([step_2])

        rule_3 = FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "checkbox"}, True]},
            trigger_from_step=step_2,
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
        # We set a value to a user-defined variable, so step 1 is assigned based on the
        # input variables.
        rule_3.form_steps.set([step_1])

        submission = SubmissionFactory.create(form=form)
        submission_step_1 = SubmissionStepFactory.create(
            submission=submission, form_step=step_1
        )
        submission_step_2 = SubmissionStepFactory.create(
            submission=submission, form_step=step_2
        )

        with self.subTest("Rules old"):
            rules = get_rules_to_evaluate(submission, submission_step_1)
            # Rule 3 is not included because of the "trigger_from_step"
            self.assertEqual(list(rules), [rule_1, rule_2])

            rules = get_rules_to_evaluate(submission, submission_step_2)
            self.assertEqual(list(rules), [rule_1, rule_2, rule_3])

        with self.subTest("Rules new"):
            form.new_logic_evaluation_enabled = True
            form.save(update_fields=["new_logic_evaluation_enabled"])

            rules = get_rules_to_evaluate(submission, submission_step_1)
            # The "trigger_from_step" on rule 3 is ignored here
            self.assertEqual(list(rules), [rule_1, rule_3])

            rules = get_rules_to_evaluate(submission, submission_step_2)
            self.assertEqual(list(rules), [rule_2])

    def test_get_rules_to_evaluate_new_iterating_over_rules_does_not_exhaust_them(self):
        """
        Ensure iterating over the rules once does not exhaust them, as we iterate
        evaluation we iterate over the rules multiple times.
        """
        form = FormFactory.create(new_logic_evaluation_enabled=True)
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

        for _ in (0, 1):
            rule = None
            for r in rules:
                rule = r
            self.assertEqual(rule, rule_2)
