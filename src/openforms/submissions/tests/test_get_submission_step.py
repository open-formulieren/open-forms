"""
Relates to Github issues #110 and #114

A form and its form step definitions are a static declaration, which can include
custom field types. The custom field types only resolve within the context of a
submission to be able to be transformed into vanilla Formio definitions.

The tests in this module validate that we can retrieve the submission-context
aware step definition.
"""

import uuid
from unittest.mock import patch

from django.test import tag

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.formio.components.vanilla import SelectBoxes, TextField
from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.formio.formatters.formio import TextFieldFormatter
from openforms.formio.registry import BasePlugin, ComponentRegistry
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
            "slug": self.step.slug,
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
        register = ComponentRegistry()
        register("selectboxes")(SelectBoxes)

        @register("textfield")
        class TextField(BasePlugin):
            formatter = TextFieldFormatter

            @staticmethod
            def mutate_config_dynamically(component, submission, data):
                component["label"] = "Rewritten label"

        self._add_submission_to_session(self.submission)

        with patch("openforms.formio.dynamic_config.register", new=register):
            response = self.client.get(self.step_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {
            "id": None,  # there is no submission step created yet
            "slug": self.step.slug,
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

    @tag("gh-1208", "gh-1068")
    def test_dynamic_config_applied(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "file",
                    "key": "file",
                    "storage": "url",
                    "url": "",  # must be set dynamically
                }
            ]
        )
        self._add_submission_to_session(submission)
        step = submission.submissionstep_set.get()
        url = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step.form_step.uuid,
            },
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        component = data["formStep"]["configuration"]["components"][0]
        self.assertEqual(component["key"], "file")
        self.assertEqual(component["type"], "file")
        self.assertEqual(component["url"], "http://testserver/api/v2/formio/fileupload")


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

    def test_it_only_translates_appropriate_string_properties(self):
        submission = SubmissionFactory.from_data(
            {"bar": "Korova Milk Bar"},
            language_code="de",
        )
        form_step = submission.steps[0].form_step
        form_step.form_definition.configuration["components"][0]["openForms"] = {
            "translations": {"de": {"label": "Kneipe"}}
        }
        form_step.form_definition.save()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )

        textfield = self.client.get(endpoint).json()["formStep"]["configuration"][
            "components"
        ][0]

        self.assertEqual(textfield["key"], "bar")
        self.assertEqual(textfield["label"], "Kneipe")

    def test_component_properties_are_translated(self):
        submission = SubmissionFactory.create(
            language_code="en",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "repeatingGroup1",
                        "label": "Herhalende groep 1",
                        "tooltip": "Tip 1",
                        "groupLabel": "Element",
                        "components": [
                            {
                                "type": "textfield",
                                "label": "Tekst 1",
                                "key": "text1",
                                "openForms": {
                                    "translations": {
                                        "en": {"label": "Text 1"},
                                        "nl": {"label": "Tekst 1"},
                                    }
                                },
                            },
                        ],
                        "openForms": {
                            "translations": {
                                "en": {
                                    "label": "Repeating group 1",
                                    "tooltip": "First tip",
                                    "groupLabel": "Item",
                                },
                                "nl": {
                                    "label": "Herhalende groep 1",
                                    "tooltip": "Tip 1",
                                    "groupLabel": "Element",
                                },
                            }
                        },
                    },
                    {
                        "type": "radio",
                        "key": "radio1",
                        "tooltip": "De uitsteekschijf van deze week",
                        "values": [
                            {
                                "value": 1,
                                "label": "Een",
                                "openForms": {
                                    "translations": {
                                        "en": {"label": "One"},
                                        "nl": {"label": "Een"},
                                    }
                                },
                            },
                            {"value": 2},
                        ],
                        "openForms": {
                            "translations": {
                                "en": {"tooltip": "Radio Giraffe's tip of the week"},
                                "nl": {"tooltip": "De uitsteekschijf van deze week"},
                            }
                        },
                    },
                    {
                        "type": "select",
                        "key": "select1",
                        "data": {
                            "values": [
                                {
                                    "value": 1,
                                    "label": "Keuze 1",
                                    "openForms": {
                                        "translations": {
                                            "en": {"label": "1st Choice"},
                                            "nl": {"label": "Keuze 1"},
                                        }
                                    },
                                },
                                {"value": 2},
                            ]
                        },
                    },
                ],
            },
        )
        self._add_submission_to_session(submission)
        form_step = submission.steps[0].form_step
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )

        configuration = self.client.get(endpoint).json()["formStep"]["configuration"]

        wrapped_configuration = FormioConfigurationWrapper(configuration)
        expected = {
            "repeatingGroup1": {
                "label": "Repeating group 1",
                "tooltip": "First tip",
                "groupLabel": "Item",
            },
            "text1": {
                "label": "Text 1",
            },
        }

        for key, translations in expected.items():
            for prop, text in translations.items():
                with self.subTest(component=key, property=prop, expected=text):
                    component = wrapped_configuration[key]

                    self.assertEqual(component[prop], text)

        self.assertEqual(wrapped_configuration["radio1"]["values"][0]["label"], "One")
        self.assertEqual(
            wrapped_configuration["radio1"]["tooltip"],
            "Radio Giraffe's tip of the week",
        )
        self.assertEqual(
            wrapped_configuration["select1"]["data"]["values"][0]["label"], "1st Choice"
        )

        # assert translation doesn't invent attributes.
        self.assertNotIn("label", wrapped_configuration["radio1"]["values"][1])
        self.assertNotIn("label", wrapped_configuration["select1"]["data"]["values"][1])

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
            form_step=step, submission=submission, data={"date1": "2022-09-13"}
        )
        SubmissionValueVariableFactory.create(
            submission=submission,
            key="userDefinedDate",
            value="2022-12-31",
            data_type=FormVariableDataTypes.date,
            form_variable__user_defined=True,
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

    def test_dynamic_date_component_config_based_on_variables_with_datetime(self):
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
            # Before the data is saved in the backend, the dates are sent from the SDK as datetimes
            data={"date1": "2022-09-13T00:00:00+02:00"},
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

    def test_custom_components_and_form_logic(self):
        # set up custom field type for test only
        register = ComponentRegistry()
        register("textfield")(TextField)

        @register("testCustomType")
        class CustomType(BasePlugin):
            formatter = TextFieldFormatter

            @staticmethod
            def mutate_config_dynamically(component, submission, data):
                key = component["key"]
                component.clear()
                component.update(
                    {
                        "type": "textfield",
                        "key": key,
                        "defaultValue": "testCustomType",
                        "validate": {
                            "required": False,
                        },
                    }
                )

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
                            "value": "validate.required",
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

        with patch("openforms.formio.dynamic_config.register", new=register):
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
                "validate": {
                    "required": True,
                },
            },
        ]
        self.assertEqual(components, expected)

    def test_empty_values_for_date_related_components(self):
        """
        Ensure empty values of date-related components are properly serialized
        (we convert them to ``None`` in our Python type domain).
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "date",
                    "key": "date",
                    "label": "Date",
                },
                {
                    "type": "time",
                    "key": "time",
                    "label": "Datetime",
                },
                {
                    "type": "datetime",
                    "key": "datetime",
                    "label": "Datetime",
                },
            ],
            submitted_data={"date": "", "time": "", "datetime": ""},
        )
        step = submission.form.formstep_set.get()
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
        self.assertEqual(
            response.json()["data"],
            {"date": "", "time": "", "datetime": ""},
        )
