from rest_framework.test import APITestCase

from openforms.formio.datastructures import FormioData
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)
from openforms.submissions.form_logic import evaluate_form_logic
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)

from ...models.submission_value_variable import (
    SubmissionValueVariable,
    SubmissionValueVariablesState,
)
from ...rendering import Renderer, RenderModes


class SubmissionVariablesPerformanceTests(APITestCase):
    def test_evaluate_form_logic_without_rules(self):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var1", "type": "textfield"},
                    {"key": "var2", "type": "textfield"},
                ]
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var3", "type": "textfield"},
                    {"key": "var4", "type": "textfield"},
                ]
            },
        )

        # ensure there is a submission
        submission = SubmissionFactory.create(form=form)
        submission.is_authenticated  # Load the auth info (otherwise an extra query is needed)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
            data={"var1": "test1", "var2": "test2"},
        )
        submission_step2 = SubmissionStepFactory.create(
            submission=submission, form_step=form_step2
        )
        submission_step2._unsaved_data = {"var3": "test3", "var4": "test4"}
        data = submission.data

        # preload the execution state, this normally happens in the viewset/calling code
        submission.load_execution_state()
        del submission._variables_state  # force re-fetching this to count queries

        # 1. Loading the variables state - fetch all the form variables
        # 2. Loading the variables state - fetch all the submission variables
        # 3. Retrieve all logic rules related to a form
        with self.assertNumQueries(3):
            evaluate_form_logic(submission, submission_step2, data)

    def test_evaluate_form_logic_with_rules(self):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var1", "type": "textfield"},
                    {"key": "var2", "type": "textfield"},
                ]
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var3", "type": "textfield"},
                    {"key": "var4", "type": "textfield"},
                ]
            },
        )

        # ensure there is a submission
        submission = SubmissionFactory.create(form=form)
        submission.is_authenticated  # Load the auth info (otherwise an extra query is needed)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
            data={"var1": "test1", "var2": "test2"},
        )
        submission_step2 = SubmissionStepFactory.create(
            submission=submission, form_step=form_step2
        )
        submission_step2._unsaved_data = {"var3": "test3", "var4": "test4"}

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "var2"}, "test2"]},
            actions=[
                {
                    "form_step_uuid": f"{form_step1.uuid}",  # Change the saved data of another step
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        data = submission.data

        # preload the execution state, this normally happens in the viewset/calling code
        submission.load_execution_state()
        del submission._variables_state  # force re-fetching this to count queries

        # 1.  Loading the variables state - fetch all the form variables
        # 2.  Loading the variables state - fetch all the submission variables
        # 3.  Retrieve all logic rules related to a form
        # 4.  Retrieve the submission variables to be deleted - deletion of data happens
        #     because the step is marked N/A
        # 5.  Retrieve the submission attachment files to be deleted
        # 6.  Delete submission values
        with self.assertNumQueries(6):
            evaluate_form_logic(submission, submission_step2, data)

    def test_update_step_data(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var1", "type": "textfield"},
                    {"key": "var2", "type": "textfield"},
                    {"key": "var3", "type": "textfield"},
                    {"key": "var4", "type": "textfield"},
                ]
            },
        )

        # ensure there is a submission
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"var1": "test1", "var2": "test2"},
        )

        # typically done in the viewset before the data is accessed
        submission.load_execution_state()

        # 1. load_variables_state: retrieve form variables
        # 2. load_variables_state: retrieve submission value variables
        # 3. bulk_create var3 and var4 submission value variables
        # 4. bulk_update var1 and var2 submission value variables
        with self.assertNumQueries(4):
            submission_step.data = FormioData(
                {
                    "var1": "test1-modified",
                    "var2": "test2-modified",
                    "var3": "test3",
                    "var4": "test4",
                }
            )

    def test_get_step_data(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var1", "type": "textfield"},
                    {"key": "var2", "type": "textfield"},
                    {"key": "var3", "type": "textfield"},
                    {"key": "var4", "type": "textfield"},
                ]
            },
        )

        # ensure there is a submission
        submission = SubmissionFactory.create(form=form)
        submission_step = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"var1": "test1", "var2": "test2"},
        )

        # typically done in the viewset before the data is accessed
        submission.load_execution_state()

        # 1. load_variables_state: retrieve form variables
        # 2. load_variables_state: retrieve submission value variables
        with self.assertNumQueries(2):
            submission_step.data

    def test_get_variables_state_no_submission_variables(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var1", "type": "textfield"},
                    {"key": "var2", "type": "textfield"},
                ]
            },
        )
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var3", "type": "textfield"},
                    {"key": "var4", "type": "textfield"},
                ]
            },
        )

        self.assertFalse(SubmissionValueVariable.objects.exists())

        # ensure there is a submission
        submission = SubmissionFactory.create(form=form)

        # typically done in the viewset before the data is accessed
        submission.load_execution_state()

        # 1. Get the form variables
        # 2. Get the submission variables
        with self.assertNumQueries(2):
            SubmissionValueVariablesState(submission).variables

    def test_get_variables_state_two_submission_variables(self):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var1", "type": "textfield"},
                    {"key": "var2", "type": "textfield"},
                ]
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var3", "type": "textfield"},
                    {"key": "var4", "type": "textfield"},
                ]
            },
        )

        # ensure there is a submission
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
            data={"var1": "test1", "var2": "test2"},
        )
        submission_step2 = SubmissionStepFactory.create(
            submission=submission, form_step=form_step2
        )
        submission_step2._unsaved_data = {"var3": "test3", "var4": "test4"}
        # typically done in the viewset before the data is accessed
        submission.load_execution_state()

        self.assertEqual(2, submission.submissionvaluevariable_set.count())

        # 1. Get the form variables
        # 2. Get the submission variables
        with self.assertNumQueries(2):
            SubmissionValueVariablesState(submission).variables

    def test_get_variables_state_all_saved_submission_variables(self):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var1", "type": "textfield"},
                    {"key": "var2", "type": "textfield"},
                ]
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var3", "type": "textfield"},
                    {"key": "var4", "type": "textfield"},
                ]
            },
        )

        # ensure there is a submission
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
            data={"var1": "test1", "var2": "test2"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step2,
            data={"var3": "test3", "var4": "test4"},
        )
        # typically done in the viewset before the data is accessed
        submission.load_execution_state()

        self.assertEqual(4, submission.submissionvaluevariable_set.count())

        # 1. Get the form variables
        # 2. Get the submission variables
        with self.assertNumQueries(2):
            SubmissionValueVariablesState(submission).variables

    def test_value_variables_state_get_data(self):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var1", "type": "textfield"},
                    {"key": "var2", "type": "textfield"},
                ]
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var3", "type": "textfield"},
                    {"key": "var4", "type": "textfield"},
                ]
            },
        )

        # ensure there is a submission
        submission = SubmissionFactory.create(form=form)
        submission_step1 = SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
            data={"var1": "test1", "var2": "test2"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step2,
            data={"var3": "test3", "var4": "test4"},
        )

        state = SubmissionValueVariablesState(submission)
        # Load variables
        state.variables

        # The queries should have been done in the get_state function
        with self.assertNumQueries(0):
            state.get_data(submission_step=submission_step1)

        with self.assertNumQueries(0):
            state.get_data()

    def test_rendering(self):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var1", "type": "textfield"},
                    {"key": "var2", "type": "textfield"},
                ]
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"key": "var3", "type": "textfield"},
                    {"key": "var4", "type": "textfield"},
                ]
            },
        )

        # ensure there is a submission
        submission = SubmissionFactory.create(form=form)
        submission.is_authenticated  # Load the auth info (otherwise an extra query is needed)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step1,
            data={"var1": "test1", "var2": "test2"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step2,
            data={"var3": "test3", "var4": "test4"},
        )
        SubmissionValueVariableFactory.create(
            key="ud1",
            value="Some data 1",
            submission=submission,
            form_variable__user_defined=True,
            form_variable__name="User defined var 1",
        )
        SubmissionValueVariableFactory.create(
            key="ud2",
            value="Some data 2",
            submission=submission,
            form_variable__user_defined=True,
            form_variable__name="User defined var 2",
        )

        renderer = Renderer(submission=submission, mode=RenderModes.pdf, as_html=True)

        # typically done in the viewset/management command before the data is accessed
        submission.load_execution_state()

        # 1. Retrieve form variables
        # 2. Retrieve submission variables
        # 3. Retrieve logic rules
        with self.assertNumQueries(3):
            nodes = [node for node in renderer]

        with self.assertNumQueries(0):
            [node.render() for node in nodes]
