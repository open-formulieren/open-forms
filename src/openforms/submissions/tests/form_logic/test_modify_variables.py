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


class VariableModificationTests(VariablesTestMixin, TestCase):
    def test_modify_variable_related_to_step_being_edited(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "nLargeBoxes",
                    },
                    {
                        "type": "number",
                        "key": "nGiganticBoxes",
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form, form_definition__configuration={"components": []}
        )
        FormVariableFactory.create(
            form=form,
            key="nTotalBoxes",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.int,
            form_definition=step2.form_definition,
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {
                        "!=": [
                            {"var": "nLargeBoxes"},
                            "",
                        ]
                    },
                    {
                        "!=": [
                            {"var": "nGiganticBoxes"},
                            "",
                        ]
                    },
                ]
            },
            actions=[
                {
                    "variable": "nTotalBoxes",
                    "action": {
                        "name": "Update variable",
                        "type": "variable",
                        "value": {
                            "+": [{"var": "nLargeBoxes"}, {"var": "nGiganticBoxes"}]
                        },
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"nLargeBoxes": 2, "nGiganticBoxes": 5},
        )
        # Step being edited
        submission_step2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
            data={},
        )

        evaluate_form_logic(submission, submission_step2, submission.data)

        updated_variable_value = submission_step2._unsaved_data.get("nTotalBoxes")

        self.assertEqual(7, updated_variable_value)

    def test_modify_variable_related_to_another_step_than_the_one_being_edited(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "nLargeBoxes",
                    },
                    {
                        "type": "number",
                        "key": "nGiganticBoxes",
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form, form_definition__configuration={"components": []}
        )
        FormVariableFactory.create(
            form=form,
            key="nTotalBoxes",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.int,
            form_definition=step1.form_definition,
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {
                        "!=": [
                            {"var": "nLargeBoxes"},
                            "",
                        ]
                    },
                    {
                        "!=": [
                            {"var": "nGiganticBoxes"},
                            "",
                        ]
                    },
                ]
            },
            actions=[
                {
                    "variable": "nTotalBoxes",
                    "action": {
                        "name": "Update variable",
                        "type": "variable",
                        "value": {
                            "+": [{"var": "nLargeBoxes"}, {"var": "nGiganticBoxes"}]
                        },
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"nLargeBoxes": 2, "nGiganticBoxes": 5},
        )
        # Step being edited
        submission_step2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
            data={},
        )

        evaluate_form_logic(submission, submission_step2, submission.data)

        self.assertEqual(7, submission_step2.data["nTotalBoxes"])

    def test_modify_variable_not_related_to_a_step(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "nLargeBoxes",
                    },
                    {
                        "type": "number",
                        "key": "nGiganticBoxes",
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form, form_definition__configuration={"components": []}
        )
        FormVariableFactory.create(
            form=form,
            key="nTotalBoxes",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.int,
            form_definition=step1.form_definition,
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {
                        "!=": [
                            {"var": "nLargeBoxes"},
                            "",
                        ]
                    },
                    {
                        "!=": [
                            {"var": "nGiganticBoxes"},
                            "",
                        ]
                    },
                ]
            },
            actions=[
                {
                    "variable": "nTotalBoxes",
                    "action": {
                        "name": "Update variable",
                        "type": "variable",
                        "value": {
                            "+": [{"var": "nLargeBoxes"}, {"var": "nGiganticBoxes"}]
                        },
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"nLargeBoxes": 2, "nGiganticBoxes": 5},
        )
        # Step being edited
        submission_step2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
            data={},
        )

        evaluate_form_logic(submission, submission_step2, submission.data)

        self.assertEqual(7, submission_step2.data["nTotalBoxes"])

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
