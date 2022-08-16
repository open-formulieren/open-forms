from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.constants import FormVariableSources
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

        # 1. get_dynamic_configuration: injects variables in configuration and *currently* does 1 query to retrieve
        #    variables with prefill data, so the defaultValue on the components can be set.
        # 2. Retrieve all logic rules related to a form
        # 3. Load submission state: Retrieve formsteps,
        # 4. Load submission state: Retrieve submission steps
        with self.assertNumQueries(4):
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

        form_step1_path = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": form_step1.uuid},
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

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "var2"}, "test2"]},
            actions=[
                {
                    "form_step": f"http://example.com{form_step1_path}",  # Change the saved data of another step
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        data = submission.data

        # 1.  get_dynamic_configuration: injects variables in configuration and *currently* does 1 query to retrieve
        #     variables with prefill data, so the defaultValue on the components can be set.
        # 2.  Retrieve all logic rules related to a form
        # 3.  Load submission state: Retrieve formsteps,
        # 4.  Load submission state: Retrieve submission steps
        # 5.  Retrieve the submission variables to be deleted
        # 6.  Retrieve the submission attachment files to be deleted
        # 7.  SAVEPOINT
        # 8.  Delete submission attachment files
        # 9.  RELEASE SAVEPOINT
        # 10. Delete submission values
        # 11. Retrieve all form_variables
        # 12. Creation of timelinelog
        with self.assertNumQueries(12):
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

        # 1. load_submission_state: retrieve form variables
        # 2. load_submission_state: retrieve submission value variables
        # 3. bulk_create var3 and var4 submission value variables
        # 4. bulk_update var1 and var2 submission value variables
        with self.assertNumQueries(4):
            submission_step.data = {
                "var1": "test1-modified",
                "var2": "test2-modified",
                "var3": "test3",
                "var4": "test4",
            }

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

        # 1. load_submission_state: retrieve form variables
        # 2. load_submission_state: retrieve submission value variables
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

        # 1. Get the submission variables that are already in the database
        # 2. Get the form variables for which there is no corresponding submission variable in the database
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

        self.assertEqual(2, submission.submissionvaluevariable_set.count())

        # 1. Get the submission variables that are already in the database
        # 2. Get the form variables for which there is no corresponding submission variable in the database
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

        self.assertEqual(4, submission.submissionvaluevariable_set.count())

        # 1. Get the submission variables that are already in the database
        # 2. Get the form variables for which there is no corresponding submission variable in the database
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
            form_variable__source=FormVariableSources.user_defined,
            form_variable__show_in_email=True,
            form_variable__show_in_pdf=True,
            form_variable__show_in_summary=True,
        )
        SubmissionValueVariableFactory.create(
            key="ud2",
            value="Some data 2",
            submission=submission,
            form_variable__source=FormVariableSources.user_defined,
            form_variable__show_in_email=False,
            form_variable__show_in_pdf=False,
            form_variable__show_in_summary=False,
        )

        renderer = Renderer(submission=submission, mode=RenderModes.pdf, as_html=True)

        # 1-2. renderer get_children: get submission data (get form variables and submission value variables)
        # 3. renderer get_children: get submission steps
        # 4. Retrieve prefill data
        # 5. Retrieve logic rules
        # 6. Load submission state: Retrieve formsteps,
        # 7. Load submission state: Retrieve submission steps
        # 8. Query if there are user defined variables
        with self.assertNumQueries(8):
            nodes = [node for node in renderer]

        with self.assertNumQueries(0):
            [node.render() for node in nodes]
