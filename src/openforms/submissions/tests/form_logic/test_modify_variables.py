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


class VariableModificationTests(TestCase):
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
            data_type=FormVariableDataTypes.float,
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

        variables_state = submission.load_submission_value_variables_state()
        variable = variables_state.variables["nTotalBoxes"]
        self.assertEqual(7, variable.value)

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
            data_type=FormVariableDataTypes.float,
            form_definition=step1.form_definition,
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {
                        "!=": [
                            {"var": "nLargeBoxes"},
                            None,
                        ]
                    },
                    {
                        "!=": [
                            {"var": "nGiganticBoxes"},
                            None,
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

        variables_state = submission.load_submission_value_variables_state()
        variable = variables_state.variables["nTotalBoxes"]
        self.assertEqual(7, variable.value)

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
            data_type=FormVariableDataTypes.float,
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

        variables_state = submission.load_submission_value_variables_state()
        variable = variables_state.variables["nTotalBoxes"]
        self.assertEqual(7, variable.value)
