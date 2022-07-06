from django.test import TestCase

from openforms.forms.constants import FormVariableDataTypes, FormVariableSources
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)

from ...form_logic import evaluate_form_logic
from ..factories import SubmissionFactory, SubmissionStepFactory
from ..mixins import VariablesTestMixin


class DeterministicEvaluationTests(VariablesTestMixin, TestCase):
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

        evaluate_form_logic(submission, submission_step, {"a": 3})

        self.assertEqual(submission_step.data["a"], 8)  # ( 3 x 2 ) + 2
