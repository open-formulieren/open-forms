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

    def test_logic_with_repeating_groups(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "cars",
                        "components": [
                            {"type": "textfield", "key": "colour"},
                            {"type": "number", "key": "price"},
                        ],
                    },
                ]
            },
        )

        FormVariableFactory.create(
            form=form,
            key="numberOfCars",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.float,
        )
        FormVariableFactory.create(
            form=form,
            key="totalPrice",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.float,
        )
        FormVariableFactory.create(
            form=form,
            key="priceOfThirdCar",
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.float,
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"!!": [True]},
            actions=[
                # Action to calculate the number of cars
                {
                    "variable": "numberOfCars",
                    "action": {
                        "type": "variable",
                        "value": {
                            "reduce": [
                                {"var": "cars"},
                                {"+": [{"var": "accumulator"}, 1]},
                                0,
                            ]
                        },
                    },
                },
                # Action to calculate the total price
                {
                    "variable": "totalPrice",
                    "action": {
                        "type": "variable",
                        "value": {
                            "reduce": [
                                {"var": "cars"},
                                {
                                    "+": [
                                        {"var": "accumulator"},
                                        {"var": "current.price"},
                                    ]
                                },
                                0,
                            ]
                        },
                    },
                },
                # Get the price of the 3rd car (which will be undefined)
                {
                    "variable": "priceOfThirdCar",
                    "action": {
                        "type": "variable",
                        "value": {"var": ["cars.2.price", 0]},
                    },
                },
            ],
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={
                "cars": [
                    {"colour": "blue", "price": 2000},
                    {"colour": "red", "price": 3000},
                ]
            },
        )

        evaluate_form_logic(submission, submission_step, submission.data)

        variables_state = submission.load_submission_value_variables_state()

        self.assertEqual(2, variables_state.variables["numberOfCars"].value)
        self.assertEqual(5000, variables_state.variables["totalPrice"].value)
        self.assertEqual(0, variables_state.variables["priceOfThirdCar"].value)
