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

        state = submission.load_submission_value_variables_state()
        self.assertEqual(state.get_data(include_unsaved=True)["nTotalBoxes"], 7)

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

        state = submission.load_submission_value_variables_state()
        self.assertEqual(state.get_data(include_unsaved=True)["nTotalBoxes"], 7)

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

        state = submission.load_submission_value_variables_state()
        self.assertEqual(state.get_data(include_unsaved=True)["nTotalBoxes"], 7)

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

        state = submission.load_submission_value_variables_state()
        data = state.get_data(include_unsaved=True)
        self.assertEqual(2, data["numberOfCars"])
        self.assertEqual(5000, data["totalPrice"])
        self.assertEqual(0, data["priceOfThirdCar"])

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

        state = submission.load_submission_value_variables_state()
        self.assertEqual(state.get_data(include_unsaved=True)["timedelta"], "P368D")

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

        state = submission.load_submission_value_variables_state()
        self.assertTrue(state.get_data(include_unsaved=True)["canApply"])

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

        state = submission.load_submission_value_variables_state()
        self.assertFalse(state.get_data(include_unsaved=True)["yo.im.nested.canApply"])

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

        state = submission.load_submission_value_variables_state()
        self.assertTrue(state.get_data(include_unsaved=True)["canApply"])

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

        state = submission.load_submission_value_variables_state()
        self.assertEqual(
            str(state.get_data(include_unsaved=True)["date"]), "2025-07-06"
        )

    def test_children_synchronization_not_allowing_selection(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "enableSelection": False,
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "components": [
                            {"type": "bsn", "key": "bsn"},
                            {"type": "textfield", "key": "childName"},
                            {"type": "textfield", "key": "affixes"},
                        ],
                    }
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": "synchronize-variables",
                        "config": {
                            "source_variable": "children",
                            "destination_variable": "editgrid",
                            "identifier_variable": "bsn",
                            "data_mappings": [
                                {
                                    "property": "bsn",
                                    "component_key": "bsn",
                                },
                                {
                                    "property": "firstNames",
                                    "component_key": "childName",
                                },
                                {
                                    "property": "affixes",
                                    "component_key": "affixes",
                                },
                            ],
                        },
                    },
                },
            ],
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={
                "children": [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__addedManually": False,
                        "__id": "07375aec-739c-4aa7-bbca-083b617248de",
                    },
                    {
                        "bsn": "999970161",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Peet",
                        "dateOfBirth": "2018-12-01",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__addedManually": False,
                        "__id": "735ea17c-58a7-4676-94fc-cf2bb4263330",
                    },
                    {
                        "bsn": "999970173",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pelle",
                        "dateOfBirth": "2017-09-01",
                        "dateOfBirthPrecision": "date",
                        "selected": None,
                        "__addedManually": False,
                        "__id": "92188604-3924-439a-995b-6ab9c2ed77ae",
                    },
                ]
            },
        )
        # Step being edited
        submission_step2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
            data={},
        )
        evaluate_form_logic(submission, submission_step2)

        state = submission.load_submission_value_variables_state()
        self.assertEqual(
            state.get_data(include_unsaved=True)["editgrid"],
            [
                {"bsn": "999970409", "childName": "Pero", "affixes": "van"},
                {"bsn": "999970161", "childName": "Peet", "affixes": "van"},
                {"bsn": "999970173", "childName": "Pelle", "affixes": "van"},
            ],
        )

    def test_children_synchronization_with_no_destination_data(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "enableSelection": True,
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "components": [
                            {"type": "bsn", "key": "bsn"},
                            {"type": "textfield", "key": "childName"},
                        ],
                    }
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": "synchronize-variables",
                        "config": {
                            "source_variable": "children",
                            "destination_variable": "editgrid",
                            "identifier_variable": "bsn",
                            "data_mappings": [
                                {
                                    "property": "bsn",
                                    "component_key": "bsn",
                                },
                                {
                                    "property": "firstNames",
                                    "component_key": "childName",
                                },
                            ],
                        },
                    },
                },
            ],
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={
                "children": [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                        "selected": False,
                        "__addedManually": False,
                        "__id": "07375aec-739c-4aa7-bbca-083b617248de",
                    },
                    {
                        "bsn": "999970161",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Peet",
                        "dateOfBirth": "2018-12-01",
                        "dateOfBirthPrecision": "date",
                        "selected": True,
                        "__addedManually": False,
                        "__id": "735ea17c-58a7-4676-94fc-cf2bb4263330",
                    },
                    {
                        "bsn": "999970173",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pelle",
                        "dateOfBirth": "2017-09-01",
                        "dateOfBirthPrecision": "date",
                        "selected": True,
                        "__addedManually": False,
                        "__id": "92188604-3924-439a-995b-6ab9c2ed77ae",
                    },
                ]
            },
        )
        # Step being edited
        submission_step2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
            data={},
        )
        evaluate_form_logic(submission, submission_step2)

        state = submission.load_submission_value_variables_state()
        self.assertEqual(
            state.get_data(include_unsaved=True)["editgrid"],
            [
                {"bsn": "999970161", "childName": "Peet"},
                {"bsn": "999970173", "childName": "Pelle"},
            ],
        )

    def test_children_synchronization_with_destination_data_update(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "enableSelection": True,
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "components": [
                            {"type": "bsn", "key": "bsn"},
                            {"type": "textfield", "key": "childName"},
                        ],
                    }
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": "synchronize-variables",
                        "config": {
                            "source_variable": "children",
                            "destination_variable": "editgrid",
                            "identifier_variable": "bsn",
                            "data_mappings": [
                                {
                                    "property": "bsn",
                                    "component_key": "bsn",
                                },
                                {
                                    "property": "firstNames",
                                    "component_key": "childName",
                                },
                            ],
                        },
                    },
                },
            ],
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={
                "children": [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                        "selected": True,
                        "__addedManually": False,
                        "__id": "07375aec-739c-4aa7-bbca-083b617248de",
                    },
                    {
                        "bsn": "999970161",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Peet",
                        "dateOfBirth": "2018-12-01",
                        "dateOfBirthPrecision": "date",
                        "selected": True,
                        "__addedManually": False,
                        "__id": "735ea17c-58a7-4676-94fc-cf2bb4263330",
                    },
                    {
                        "bsn": "999970173",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pelle",
                        "dateOfBirth": "2017-09-01",
                        "dateOfBirthPrecision": "date",
                        "selected": False,
                        "__addedManually": False,
                        "__id": "92188604-3924-439a-995b-6ab9c2ed77ae",
                    },
                ]
            },
        )
        # Step being edited
        # We already have data and we modify the selected children of the previous step
        submission_step2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
            data={
                "editgrid": [
                    {"bsn": "999970409", "childName": "Pero"},
                    {"bsn": "999970173", "childName": "Pelle"},
                ]
            },
        )
        evaluate_form_logic(submission, submission_step2)

        state = submission.load_submission_value_variables_state()
        self.assertEqual(
            state.get_data(include_unsaved=True)["editgrid"],
            [
                {"bsn": "999970409", "childName": "Pero"},
                {"bsn": "999970161", "childName": "Peet"},
            ],
        )

    def test_children_synchronization_with_no_destination_and_source_data(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "children",
                        "key": "children",
                        "enableSelection": True,
                    },
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "components": [
                            {"type": "bsn", "key": "bsn"},
                            {"type": "textfield", "key": "childName"},
                        ],
                    }
                ]
            },
        )
        FormVariableFactory.create(
            key="children_immutable",
            form=form,
            user_defined=True,
            prefill_plugin="family_members",
            prefill_options={
                "type": "children",
                "mutable_data_form_variable": "children",
                "min_age": None,
                "max_age": None,
            },
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": "synchronize-variables",
                        "config": {
                            "source_variable": "children",
                            "destination_variable": "editgrid",
                            "identifier_variable": "bsn",
                            "data_mappings": [
                                {
                                    "property": "bsn",
                                    "component_key": "bsn",
                                },
                                {
                                    "property": "firstNames",
                                    "component_key": "childName",
                                },
                            ],
                        },
                    },
                },
            ],
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"children": []},
        )
        # Step being edited
        # We already have data and we modify the selected children of the previous step
        submission_step2 = SubmissionStepFactory.build(
            submission=submission,
            form_step=step2,
            data={},
        )
        evaluate_form_logic(submission, submission_step2)

        state = submission.load_submission_value_variables_state()
        self.assertEqual(state.get_data(include_unsaved=True)["editgrid"], [])
