"""
Relates to Github issues #110 and #114

A form and its form step definitions are a static declaration, which can include
custom field types. The custom field types only resolve within the context of a
submission to be able to be transformed into vanilla Formio definitions.

The tests in this module validate that we can retrieve the submission-context
aware step definition.
"""
import uuid

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.forms.custom_field_types import register, unregister
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)
from openforms.variables.constants import FormVariableDataTypes

from ..models import Submission
from .factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)
from .mixins import SubmissionsMixin


class ReadSubmissionStepTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # ensure there is a form definition
        configuration = {
            "components": [
                {
                    "label": "Some field",
                    "key": "someField",
                    "type": "textfield",
                },
                {
                    "label": "Other field",
                    "key": "otherField",
                    "type": "selectboxes",
                    "inputType": "checkbox",
                },
            ]
        }
        cls.step = FormStepFactory.create(form_definition__configuration=configuration)
        cls.submission = SubmissionFactory.create(form=cls.step.form)
        cls.step_url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": cls.submission.uuid, "step_uuid": cls.step.uuid},
        )

    def test_submission_not_in_session(self):
        with self.subTest(case="no submissions in session"):
            response = self.client.get(self.step_url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest(case="other submission in session"):
            # add another submission to the session
            other_submission = SubmissionFactory.create(form=self.step.form)
            self._add_submission_to_session(other_submission)

            response = self.client.get(self.step_url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_static_form_definition(self):
        self._add_submission_to_session(self.submission)

        response = self.client.get(self.step_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {
            "id": None,  # there is no submission step created yet
            "slug": self.step.form_definition.slug,
            "formStep": {
                "index": 0,
                "configuration": {
                    "components": [
                        {
                            "label": "Some field",
                            "key": "someField",
                            "type": "textfield",
                        },
                        {
                            "label": "Other field",
                            "key": "otherField",
                            "type": "selectboxes",
                            "inputType": "checkbox",
                        },
                    ]
                },
            },
            "data": {},
            "isApplicable": True,
            "completed": False,
            "canSubmit": True,
        }
        self.assertEqual(response.json(), expected)

    def test_dynamic_form_definition(self):
        @register("textfield")
        def custom_handler(component: dict, request, submission):
            component["label"] = "Rewritten label"
            return component

        self.addCleanup(lambda: unregister("textfield"))
        self._add_submission_to_session(self.submission)

        response = self.client.get(self.step_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {
            "id": None,  # there is no submission step created yet
            "slug": self.step.form_definition.slug,
            "formStep": {
                "index": 0,
                "configuration": {
                    "components": [
                        {
                            "label": "Rewritten label",
                            "key": "someField",
                            "type": "textfield",
                        },
                        {
                            "label": "Other field",
                            "type": "selectboxes",
                            "key": "otherField",
                            "inputType": "checkbox",
                        },
                    ]
                },
            },
            "data": {},
            "isApplicable": True,
            "completed": False,
            "canSubmit": True,
        }
        self.assertEqual(response.json(), expected)

    def test_invalid_submission_id(self):
        self._add_submission_to_session(self.submission)
        Submission.objects.filter(id=self.submission.id).delete()

        response = self.client.get(self.step_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_step_id(self):
        self._add_submission_to_session(self.submission)
        step_url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": self.submission.uuid, "step_uuid": uuid.uuid4()},
        )

        response = self.client.get(step_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_step_data_returned(self):
        self._add_submission_to_session(self.submission)
        self.assertFalse(self.submission.submissionstep_set.exists())

        # create submission step data
        SubmissionStepFactory.create(
            submission=self.submission,
            form_step=self.step,
            data={"someField": "data"},
        )

        response = self.client.get(self.step_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["data"],
            {"someField": "data"},
        )


class GetSubmissionStepTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [{"type": "textfield", "key": "field1"}]
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
        )
        form_step3 = FormStepFactory.create(
            form=form,
        )

        submission = SubmissionFactory.create(form=form)
        cls.submission_step1 = SubmissionStepFactory.create(
            form_step=form_step1, submission=submission, data={"field1": "data1"}
        )

        cls.form_step1 = form_step1
        cls.form_step2 = form_step2
        cls.form_step3 = form_step3
        cls.submission = submission

    def test_step_retrieved_if_previous_steps_completed(self):
        url = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.form_step2.uuid,
            },
        )

        self._add_submission_to_session(self.submission)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_step_retrieved_if_no_previous_steps(self):
        url = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.form_step1.uuid,
            },
        )

        self._add_submission_to_session(self.submission)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_error_raised_if_previous_step_not_completed_for_non_admin(self):
        url = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.form_step3.uuid,  # Step 2 is not completed yet!
            },
        )

        self._add_submission_to_session(self.submission)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_step_retrieved_if_not_completed_for_superuser(self):
        user = SuperUserFactory.create()
        self.client.force_login(user=user)
        url = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.form_step3.uuid,  # Step 2 is not completed yet!
            },
        )

        self._add_submission_to_session(self.submission)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_step_retrieved_if_not_completed_for_staff_with_permission(self):
        user = StaffUserFactory.create(user_permissions=["forms.change_form"])
        self.client.force_login(user=user)
        url = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.form_step3.uuid,  # Step 2 is not completed yet!
            },
        )

        self._add_submission_to_session(self.submission)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_step_retrieved_if_previous_steps_completed_with_not_applicable_steps(self):
        form = FormFactory.create()
        form_step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [{"type": "textfield", "key": "field1"}]
            },
        )
        form_step2 = FormStepFactory.create(
            form=form,
        )
        form_step3 = FormStepFactory.create(
            form=form,
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "==": [
                    {"var": "field1"},
                    "trigger-value",
                ]
            },
            actions=[
                {
                    "form_step_uuid": f"{form_step2.uuid}",
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            form_step=form_step1,
            submission=submission,
            data={"field1": "trigger-value"},
        )

        # Step 2 is not applicable with the submitted data, so retrieving step 3 should succeed
        url = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step3.uuid,
            },
        )

        self._add_submission_to_session(submission)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)


class IntegrationTests(SubmissionsMixin, APITestCase):
    """
    Integration tests where various subsystems come together.
    """

    def test_dynamic_date_component_config_based_on_variables(self):
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "date",
                        "key": "date1",
                    },
                    {
                        "type": "date",
                        "key": "date2",
                        "openForms": {
                            "minDate": {
                                "mode": "relativeToVariable",
                                "variable": "date1",
                                "operator": "add",
                                "delta": {"days": 7},
                            },
                            "maxDate": {
                                "mode": "relativeToVariable",
                                "variable": "userDefinedDate",
                            },
                        },
                    },
                ]
            },
        )
        step = form.formstep_set.get()
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            form_step=step,
            submission=submission,
            data={"date1": "2022-09-13T00:00:00+01:00"},
        )
        SubmissionValueVariableFactory.create(
            submission=submission,
            key="userDefinedDate",
            form_variable__user_defined=True,
            form_variable__data_type=FormVariableDataTypes.datetime,
            value="2022-12-31T00:00:00+01:00",
        )
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )
        self._add_submission_to_session(submission)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        date2 = response.json()["formStep"]["configuration"]["components"][1]

        self.assertEqual(date2["datePicker"]["minDate"], "2022-09-20T00:00:00+02:00")
        self.assertEqual(date2["datePicker"]["maxDate"], "2022-12-31T00:00:00+01:00")

    def test_custom_components_and_form_logic(self):

        # set up custom field type for test only
        self.addCleanup(lambda: unregister("testCustomType"))

        @register("testCustomType")
        def custom_type(component, request, submission):
            return {
                "type": "textfield",
                "key": component["key"],
                "defaultValue": "testCustomType",
                "hidden": False,
            }

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "someInput",
                    },
                    {
                        "type": "testCustomType",
                        "key": "testCustomType",
                    },
                ]
            },
        )
        step = form.formstep_set.get()
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "someInput"}, "hide-custom-field"]},
            actions=[
                {
                    "component": "testCustomType",
                    "action": {
                        "type": "property",
                        "property": {
                            "value": "hidden",
                            "type": "bool",
                        },
                        "state": True,
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            form_step=step,
            submission=submission,
            data={"someInput": "hide-custom-field"},
        )
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.uuid,
            },
        )
        self._add_submission_to_session(submission)

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        components = response.data["form_step"]["configuration"]["components"]
        expected = [
            {
                "type": "textfield",
                "key": "someInput",
            },
            {
                "type": "textfield",
                "key": "testCustomType",
                "defaultValue": "testCustomType",
                "hidden": True,
            },
        ]
        self.assertEqual(components, expected)
