from unittest.mock import patch

from django.test import TestCase

import requests_mock
from django_camunda.models import CamundaConfig

from openforms.forms.constants import LogicActionTypes
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

        evaluate_form_logic(submission, submission_step2)

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

        evaluate_form_logic(submission, submission_step2)

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

        evaluate_form_logic(submission, submission_step2)

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

        evaluate_form_logic(submission, submission_step)

        variables_state = submission.load_submission_value_variables_state()

        self.assertEqual(2, variables_state.variables["numberOfCars"].value)
        self.assertEqual(5000, variables_state.variables["totalPrice"].value)
        self.assertEqual(0, variables_state.variables["priceOfThirdCar"].value)

    def test_dates_and_timedeltas(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "date",
                        "key": "datum",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            key="timedelta",
            data_type=FormVariableDataTypes.string,
            user_defined=True,
            form=form,
            initial_value="",
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "timedelta",
                    "action": {
                        "type": "variable",
                        "value": {
                            "-": [{"date": {"var": "datum"}}, {"date": "2022-09-09"}]
                        },
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            data={"datum": "2023-09-12"},
        )

        evaluate_form_logic(submission, submission_step)

        variables_state = submission.load_submission_value_variables_state()

        self.assertEqual("P368D", variables_state.variables["timedelta"].value)

    @requests_mock.Mocker()
    def test_evaluate_dmn_action(self, m):
        m.get(
            "https://camunda.example.com/engine-rest/decision-definition?key=determine-can-apply&version=1",
            json=[
                {
                    "id": "determine-can-apply:1:06152ee5-bf59-11ee-830a-0242ac110003",
                    "key": "determine-can-apply",
                    "category": "http://camunda.org/schema/1.0/dmn",
                    "name": "Determine if can apply",
                    "version": 1,
                    "resource": "table-determine-can-apply.dmn",
                    "deploymentId": "06135a22-bf59-11ee-830a-0242ac110003",
                    "tenantId": None,
                    "decisionRequirementsDefinitionId": None,
                    "decisionRequirementsDefinitionKey": None,
                    "historyTimeToLive": 1,
                    "versionTag": None,
                }
            ],
        )
        m.post(
            "https://camunda.example.com/engine-rest/decision-definition/determine-can-apply:1:06152ee5-bf59-11ee-830a-0242ac110003/evaluate",
            json=[{"canApplyDMN": {"type": "Boolean", "value": True, "valueInfo": {}}}],
        )

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "age",
                    },
                    {
                        "type": "number",
                        "key": "income",
                    },
                    {
                        "type": "checkbox",
                        "key": "canApply",
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "input_mapping": [
                                {"form_variable": "age", "dmn_variable": "ageDMN"},
                                {
                                    "form_variable": "income",
                                    "dmn_variable": "incomeDMN",
                                },
                            ],
                            "output_mapping": [
                                {
                                    "form_variable": "canApply",
                                    "dmn_variable": "canApplyDMN",
                                }
                            ],
                            "decision_definition_id": "determine-can-apply",
                            "decision_definition_version": "1",
                            "plugin_id": "camunda7",
                        },
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            data={"age": 29, "income": 40000},
        )

        with patch(
            "openforms.dmn.contrib.camunda.checks.CamundaConfig.get_solo",
            return_value=CamundaConfig(
                enabled=True,
                root_url="https://camunda.example.com",
                rest_api_path="engine-rest/",
            ),
        ):
            evaluate_form_logic(submission, submission_step)

        variables_state = submission.load_submission_value_variables_state()

        self.assertTrue(variables_state.variables["canApply"].value)

    @requests_mock.Mocker()
    def test_evaluate_dmn_with_nested_variables(self, m):
        m.get(
            "https://camunda.example.com/engine-rest/decision-definition?key=determine-can-apply&version=1",
            json=[
                {
                    "id": "determine-can-apply:1:06152ee5-bf59-11ee-830a-0242ac110003",
                    "key": "determine-can-apply",
                    "category": "http://camunda.org/schema/1.0/dmn",
                    "name": "Determine if can apply",
                    "version": 1,
                    "resource": "table-determine-can-apply.dmn",
                    "deploymentId": "06135a22-bf59-11ee-830a-0242ac110003",
                    "tenantId": None,
                    "decisionRequirementsDefinitionId": None,
                    "decisionRequirementsDefinitionKey": None,
                    "historyTimeToLive": 1,
                    "versionTag": None,
                }
            ],
        )
        m.post(
            "https://camunda.example.com/engine-rest/decision-definition/determine-can-apply:1:06152ee5-bf59-11ee-830a-0242ac110003/evaluate",
            json=[
                {"canApplyDMN": {"type": "Boolean", "value": False, "valueInfo": {}}}
            ],
        )

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "container1",
                        "type": "fieldset",
                        "components": [
                            {
                                "type": "number",
                                "key": "age",
                            }
                        ],
                    },
                    {
                        "type": "columns",
                        "key": "container2",
                        "columns": [
                            {
                                "components": [
                                    {
                                        "type": "number",
                                        "key": "income",
                                    }
                                ]
                            }
                        ],
                    },
                    {
                        "type": "checkbox",
                        "key": "yo.im.nested.canApply",
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "input_mapping": [
                                {"form_variable": "age", "dmn_variable": "ageDMN"},
                                {
                                    "form_variable": "income",
                                    "dmn_variable": "incomeDMN",
                                },
                            ],
                            "output_mapping": [
                                {
                                    "form_variable": "yo.im.nested.canApply",
                                    "dmn_variable": "canApplyDMN",
                                },
                            ],
                            "decision_definition_id": "determine-can-apply",
                            "decision_definition_version": "1",
                            "plugin_id": "camunda7",
                        },
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            data={"age": 29, "income": 40000},
        )

        with patch(
            "openforms.dmn.contrib.camunda.checks.CamundaConfig.get_solo",
            return_value=CamundaConfig(
                enabled=True,
                root_url="https://camunda.example.com",
                rest_api_path="engine-rest/",
            ),
        ):
            evaluate_form_logic(submission, submission_step)

        variables_state = submission.load_submission_value_variables_state()

        self.assertFalse(variables_state.variables["yo.im.nested.canApply"].value)

    @requests_mock.Mocker()
    def test_evaluate_dmn_action_returns_empty_data(self, m):
        m.get(
            "https://camunda.example.com/engine-rest/decision-definition?key=determine-can-apply&version=1",
            json=[
                {
                    "id": "determine-can-apply:1:06152ee5-bf59-11ee-830a-0242ac110003",
                    "key": "determine-can-apply",
                    "category": "http://camunda.org/schema/1.0/dmn",
                    "name": "Determine if can apply",
                    "version": 1,
                    "resource": "table-determine-can-apply.dmn",
                    "deploymentId": "06135a22-bf59-11ee-830a-0242ac110003",
                    "tenantId": None,
                    "decisionRequirementsDefinitionId": None,
                    "decisionRequirementsDefinitionKey": None,
                    "historyTimeToLive": 1,
                    "versionTag": None,
                }
            ],
        )
        # If the data doesn't match any of the rules in the decision table, then an empty array is returned.
        m.post(
            "https://camunda.example.com/engine-rest/decision-definition/determine-can-apply:1:06152ee5-bf59-11ee-830a-0242ac110003/evaluate",
            json=[],
        )

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "number",
                        "key": "age",
                    },
                    {
                        "type": "number",
                        "key": "income",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            source=FormVariableSources.user_defined,
            key="canApply",
            data_type=FormVariableDataTypes.boolean,
            initial_value=True,
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.evaluate_dmn,
                        "config": {
                            "input_mapping": [
                                {"form_variable": "age", "dmn_variable": "ageDMN"},
                                {
                                    "form_variable": "income",
                                    "dmn_variable": "incomeDMN",
                                },
                            ],
                            "output_mapping": [
                                {
                                    "form_variable": "canApply",
                                    "dmn_variable": "canApplyDMN",
                                },
                            ],
                            "decision_definition_id": "determine-can-apply",
                            "decision_definition_version": "1",
                            "plugin_id": "camunda7",
                        },
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            data={"age": 29, "income": 40000},
        )

        with patch(
            "openforms.dmn.contrib.camunda.checks.CamundaConfig.get_solo",
            return_value=CamundaConfig(
                enabled=True,
                root_url="https://camunda.example.com",
                rest_api_path="engine-rest/",
            ),
        ):
            evaluate_form_logic(submission, submission_step)

        variables_state = submission.load_submission_value_variables_state()

        self.assertTrue(variables_state.variables["canApply"].value)

    def test_two_actions_on_the_same_variable(self):
        """
        Assert that it is possible to execute two consecutive actions on the same
        variable. It ensures that the returns from jsonLogic calls are converted to
        the Python-type domain (date object in this case).
        """
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "date", "key": "date"},
                ]
            },
        )
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"date": ""},
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "date",
                    "action": {
                        "type": "variable",
                        "value": "2025-06-06",
                    },
                },
                {
                    "variable": "date",
                    "action": {
                        "type": "variable",
                        "value": {"+": [{"var": "date"}, {"duration": "P1M"}]},
                    },
                },
            ],
        )

        evaluate_form_logic(submission, submission_step)

        variables_state = submission.load_submission_value_variables_state()

        self.assertEqual(str(variables_state.variables["date"].value), "2025-07-06")
