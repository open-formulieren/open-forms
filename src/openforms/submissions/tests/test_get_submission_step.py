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
from django.utils.translation import gettext_lazy as _

from freezegun import freeze_time
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
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableDataTypes

from ...config.models import GlobalConfiguration
from ..models import Submission
from .factories import (
    SubmissionFactory,
    SubmissionStepFactory,
    SubmissionValueVariableFactory,
)
from .mixins import SubmissionsMixin


class ReadSubmissionStepTests(SubmissionsMixin, APITestCase):
    maxDiff = None

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
            "formStepUuid": str(self.step.uuid),
            "slug": self.step.slug,
            "defaultConfiguration": {
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
                    },
                ],
            },
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
                    },
                ]
            },
            "data": {},
            "canSubmit": True,
            "requireBackendLogicEvaluation": False,
            "logicRules": [],
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
            "formStepUuid": str(self.step.uuid),
            "slug": self.step.slug,
            "defaultConfiguration": {
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
                    },
                ]
            },
            "configuration": {
                "components": [
                    {
                        "label": "Rewritten label",
                        "key": "someField",
                        "type": "textfield",
                    },
                    {
                        "label": "Other field",
                        "key": "otherField",
                        "type": "selectboxes",
                    },
                ]
            },
            "data": {},
            "canSubmit": True,
            # wrong but our introspection code is not aware of this ad-hoc plugin
            "requireBackendLogicEvaluation": False,
            "logicRules": [],
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
        component = data["configuration"]["components"][0]
        self.assertEqual(component["key"], "file")
        self.assertEqual(component["type"], "file")
        self.assertEqual(component["url"], "http://testserver/api/v2/formio/fileupload")


class GetSubmissionStepTests(SubmissionsMixin, APITestCase):
    maxDiff = None

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
        form.apply_logic_analysis()

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

    maxDiff = None

    def test_it_only_translates_appropriate_string_properties(self):
        submission = SubmissionFactory.from_components(
            [{"type": "textfield", "key": "bar", "label": "Bar"}],
            submitted_data={"bar": "Korova Milk Bar"},
            language_code="de",
        )
        form_step = submission.steps[0].form_step
        assert form_step is not None
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

        textfield = self.client.get(endpoint).json()["configuration"]["components"][0]

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

        configuration = self.client.get(endpoint).json()["configuration"]

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
        date2 = response.json()["configuration"]["components"][1]

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
        date2 = response.json()["configuration"]["components"][1]

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
        form.apply_logic_analysis()
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

        with (
            patch("openforms.formio.dynamic_config.register", new=register),
            patch("openforms.formio.visibility.register", new=register),
        ):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        components = response.data["configuration"]["components"]
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

    @patch(
        "openforms.formio.components.vanilla.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            form_upload_default_file_types=["image/png", "application/pdf"]
        ),
    )
    def test_default_configuration_has_components_rewritten_for_request(
        self, m_get_solo
    ):
        step = FormStepFactory.create(
            form__new_logic_evaluation_enabled=True,
            form_definition__configuration={
                "components": [
                    {
                        "type": "file",
                        "key": "file",
                        "label": "File",
                        "useConfigFiletypes": True,
                        "filePattern": "*",
                        "url": "",
                        "file": {"allowedTypesLabels": []},
                    }
                ]
            },
        )
        submission = SubmissionFactory.create(form=step.form)
        url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        self._add_submission_to_session(submission)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        expected = {
            "type": "file",
            "key": "file",
            "label": "File",
            "useConfigFiletypes": True,
            "filePattern": "image/png,application/pdf",
            "url": "http://testserver/api/v2/formio/fileupload",
            "file": {"allowedTypesLabels": [".png", ".pdf"]},
        }
        self.assertEqual(
            expected, response.json()["defaultConfiguration"]["components"][0]
        )

    def test_without_logic_rules_and_without_dynamic_configuration(self):
        step = FormStepFactory.create(
            form__new_logic_evaluation_enabled=True,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "Textfield"}
                ]
            },
        )

        submission = SubmissionFactory.create(form=step.form)
        url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        self._add_submission_to_session(submission)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        expected = {
            "id": None,  # there is no submission step created yet
            "formStepUuid": str(step.uuid),
            "slug": step.slug,
            "defaultConfiguration": {
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                ]
            },
            "configuration": {
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                ]
            },
            "data": {},
            "canSubmit": True,
            "requireBackendLogicEvaluation": False,
            "logicRules": [],
        }
        self.assertEqual(expected, response.json())

    def test_without_logic_rules_but_with_dynamic_configuration(self):
        step = FormStepFactory.create(
            form__new_logic_evaluation_enabled=True,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "{{ foo }}"}
                ]
            },
        )
        FormVariableFactory.create(
            form=step.form,
            key="foo",
            data_type=FormVariableDataTypes.string,
            user_defined=True,
            initial_value="I am a label!",
        )

        submission = SubmissionFactory.create(form=step.form)
        url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        self._add_submission_to_session(submission)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        expected = {
            "id": None,  # there is no submission step created yet
            "formStepUuid": str(step.uuid),
            "slug": step.slug,
            "defaultConfiguration": None,
            "configuration": {
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "I am a label!"},
                ]
            },
            "data": {},
            "canSubmit": True,
            "requireBackendLogicEvaluation": True,
            "logicRules": [],
        }
        self.assertEqual(expected, response.json())

    @freeze_time("2026-03-18")
    def test_with_logic_rule_that_does_not_require_backend(self):
        step = FormStepFactory.create(
            form__new_logic_evaluation_enabled=True,
            form_definition__configuration={
                "components": [
                    {"type": "date", "key": "dateOfBirth", "label": "Date of birth"},
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                ]
            },
        )
        FormLogicFactory.create(
            form=step.form,
            json_logic_trigger={"==": [{"var": "dateOfBirth"}, {"var": "today"}]},
            actions=[
                {
                    "action": {
                        "type": "variable",
                        "value": "foo",
                    },
                    "variable": "textfield",
                    "uuid": "3798727a-ae54-4661-93ad-37d873c4d5fc",
                },
                {
                    "action": {"type": "set-registration-backend", "value": "zgw-api"},
                    "uuid": "d24c8761-3a1b-4b4f-8cb0-aa9d8ec858ed",
                },
            ],
        )
        step.form.apply_logic_analysis()

        submission = SubmissionFactory.create(form=step.form)
        url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        self._add_submission_to_session(submission)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        expected = {
            "id": None,  # there is no submission step created yet
            "formStepUuid": str(step.uuid),
            "slug": step.slug,
            "defaultConfiguration": {
                "components": [
                    {"type": "date", "key": "dateOfBirth", "label": "Date of birth"},
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                ]
            },
            "configuration": {
                "components": [
                    {
                        "type": "date",
                        "key": "dateOfBirth",
                        "label": "Date of birth",
                        "placeholder": _("dd-mm-yyyy"),
                    },
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                ]
            },
            "data": {},
            "canSubmit": True,
            "requireBackendLogicEvaluation": False,
            "logicRules": [
                {
                    # Note the partially evaluated rule with added data-type
                    # information.
                    "jsonLogicTrigger": {
                        "==": [
                            {"date": [{"var": ["dateOfBirth"]}]},
                            {"date": ["2026-03-18"]},
                        ]
                    },
                    "actions": [
                        {
                            "uuid": "3798727a-ae54-4661-93ad-37d873c4d5fc",
                            "formStepUuid": None,
                            "action": {"type": "variable", "value": "foo"},
                            "variable": "textfield",
                        }
                    ],
                }
            ],
        }
        self.assertEqual(expected, response.json())

    def test_with_logic_rule_that_does_not_require_backend_but_with_dynamic_configuration(
        self,
    ):
        step = FormStepFactory.create(
            form__new_logic_evaluation_enabled=True,
            form_definition__configuration={
                "components": [
                    {"type": "date", "key": "dateOfBirth", "label": "Date of birth"},
                    {"type": "textfield", "key": "textfield", "label": "{{ foo }}"},
                ]
            },
        )
        FormVariableFactory.create(
            form=step.form,
            key="foo",
            data_type=FormVariableDataTypes.string,
            user_defined=True,
            initial_value="I am a label!",
        )
        FormLogicFactory.create(
            form=step.form,
            json_logic_trigger={"==": [{"var": "dateOfBirth"}, {"var": "today"}]},
            actions=[
                {
                    "action": {
                        "type": "variable",
                        "value": "foo",
                    },
                    "variable": "textfield",
                    "uuid": "3798727a-ae54-4661-93ad-37d873c4d5fc",
                }
            ],
        )
        step.form.apply_logic_analysis()

        submission = SubmissionFactory.create(form=step.form)
        url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        self._add_submission_to_session(submission)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        expected = {
            "id": None,  # there is no submission step created yet
            "formStepUuid": str(step.uuid),
            "slug": step.slug,
            "defaultConfiguration": None,
            "configuration": {
                "components": [
                    {
                        "type": "date",
                        "key": "dateOfBirth",
                        "label": "Date of birth",
                        "placeholder": _("dd-mm-yyyy"),
                    },
                    {"type": "textfield", "key": "textfield", "label": "I am a label!"},
                ]
            },
            "data": {},
            "canSubmit": True,
            "requireBackendLogicEvaluation": True,
            "logicRules": [],  # logic rules are not serialized when the backend is required
        }
        self.assertEqual(expected, response.json())

    def test_with_logic_rule_that_requires_backend(self):
        step = FormStepFactory.create(
            form__new_logic_evaluation_enabled=True,
            form_definition__configuration={
                "components": [
                    {"type": "date", "key": "dateOfBirth", "label": "Date of birth"},
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                ]
            },
        )
        FormVariableFactory.create(
            form=step.form,
            key="foo",
            data_type=FormVariableDataTypes.string,
            user_defined=True,
            initial_value="",
        )
        # Note that user-defined variables cannot be set in the frontend
        FormLogicFactory.create(
            form=step.form,
            json_logic_trigger={"==": [{"var": "dateOfBirth"}, {"var": "today"}]},
            actions=[
                {
                    "action": {
                        "type": "variable",
                        "value": "bar",
                    },
                    "variable": "foo",
                    "uuid": "3798727a-ae54-4661-93ad-37d873c4d5fc",
                }
            ],
        )
        step.form.apply_logic_analysis()

        submission = SubmissionFactory.create(form=step.form)
        url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        self._add_submission_to_session(submission)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        expected = {
            "id": None,  # there is no submission step created yet
            "formStepUuid": str(step.uuid),
            "slug": step.slug,
            "defaultConfiguration": None,
            "configuration": {
                "components": [
                    {
                        "type": "date",
                        "key": "dateOfBirth",
                        "label": "Date of birth",
                        "placeholder": _("dd-mm-yyyy"),
                    },
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                ]
            },
            "data": {},
            "canSubmit": True,
            "requireBackendLogicEvaluation": True,
            "logicRules": [],  # logic rules are not serialized when the backend is required
        }
        self.assertEqual(expected, response.json())

    @freeze_time("2026-03-18")
    def test_logic_rule_is_serialized_properly(self):
        form = FormFactory.create(new_logic_evaluation_enabled=True)
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "number", "key": "number", "label": "Number"},
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "date", "key": "dateOfBirth", "label": "Date of birth"},
                    {
                        "type": "content",
                        "key": "content",
                        "html": "I am some content!",
                        "hidden": False,
                    },
                ]
            },
        )
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "textfield", "label": "Textfield"},
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            key="foo",
            data_type=FormVariableDataTypes.string,
            user_defined=True,
            initial_value="",
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={
                "and": [
                    {"==": [{"var": "number"}, 42]},
                    {"==": [{"var": "dateOfBirth"}, {"var": "today"}]},
                    # This is a weird trigger because a field from a future step (3)
                    # affects something on the current step (2), but it demonstrates the
                    # principle of partial evaluation with unsaved variables.
                    {"==": [{"var": "textfield"}, ""]},
                ]
            },
            actions=[
                {
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": False,
                    },
                    "component": "content",
                    "uuid": "3798727a-ae54-4661-93ad-37d873c4d5fc",
                }
            ],
        )
        form.apply_logic_analysis()

        # Simulate submitting step 1
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step_1,
            data={"number": 42},
        )

        url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step_2.uuid},
        )
        self._add_submission_to_session(submission)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        expected = {
            "jsonLogicTrigger": {
                "and": [
                    # {"==": [{"var": "number"}, 42]} evaluates to True with the already submitted data
                    True,
                    # data-type information is added and static variables are substituted
                    {
                        "==": [
                            {"date": [{"var": ["dateOfBirth"]}]},
                            {"date": ["2026-03-18"]},
                        ]
                    },
                    # {"==": [{"var": "textfield"}, ""]} evaluates to True with the empty value
                    True,
                ]
            },
            "actions": [
                {
                    "action": {
                        "property": {"type": "bool", "value": "hidden"},
                        "state": False,
                        "type": "property",
                    },
                    "component": "content",
                    "formStepUuid": None,
                    "uuid": "3798727a-ae54-4661-93ad-37d873c4d5fc",
                }
            ],
        }
        data = response.json()
        self.assertFalse(data["requireBackendLogicEvaluation"])
        self.assertEqual(expected, data["logicRules"][0])

    @freeze_time("2026-03-18")
    def test_with_date_trigger_that_could_be_partially_resolved(self):
        step = FormStepFactory.create(
            form__new_logic_evaluation_enabled=True,
            form_definition__configuration={
                "components": [
                    {"type": "date", "key": "dateOfBirth", "label": "Date of birth"},
                ]
            },
        )
        # This is an actual logic rule used by municipalities!
        FormLogicFactory.create(
            form=step.form,
            json_logic_trigger={
                ">": [
                    {"date": {"var": "dateOfBirth"}},
                    {"date": {"-": [{"var": "today"}, {"duration": "P24Y"}]}},
                ]
            },
            actions=[
                {
                    "action": {"type": "disable-next"},
                    "form_step_uuid": str(step.uuid),
                }
            ],
        )
        step.form.apply_logic_analysis()

        submission = SubmissionFactory.create(form=step.form)
        url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        self._add_submission_to_session(submission)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # Even though the second part of the comparison could be evaluated to a date
        # already, we would lose typing information if it was. The date object would
        # be serialized to an ISO string in this case, without any remaining date
        # operation being present.
        expected = {
            ">": [
                {"date": [{"var": ["dateOfBirth"]}]},
                {"date": [{"-": [{"date": ["2026-03-18"]}, {"duration": ["P24Y"]}]}]},
            ]
        }
        self.assertEqual(expected, response.json()["logicRules"][0]["jsonLogicTrigger"])

    def test_variable_action_with_json_logic_expression_as_value(self):
        form = FormFactory.create(new_logic_evaluation_enabled=True)
        step_1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "isoDuration", "label": "ISO duration"}
                ]
            },
        )
        step_2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "date", "key": "dateOfBirth", "label": "Date of birth"},
                    {
                        "type": "date",
                        "key": "dateOfBirthMinusDuration",
                        "label": "Date of birth minus duration",
                    },
                ]
            },
        )
        # This is an actual logic rule used by municipalities!
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": "variable",
                        "value": {
                            "-": [
                                {"var": "dateOfBirth"},
                                {"duration": {"var": "isoDuration"}},
                            ]
                        },
                    },
                    "variable": "dateOfBirthMinusDuration",
                }
            ],
        )
        form.apply_logic_analysis()

        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        # Simulate submitting step 1
        SubmissionStepFactory.create(
            form_step=step_1, submission=submission, data={"isoDuration": "P18Y"}
        )

        # Get step 2
        url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step_2.uuid},
        )
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        # The "dateOfBrith" variable should have the date operator added to it, and the
        # "isoDuration" variable should be prefilled because it was already submitted
        # on the previous step.
        expected = {"-": [{"date": [{"var": ["dateOfBirth"]}]}, {"duration": ["P18Y"]}]}
        self.assertEqual(
            expected, response.json()["logicRules"][0]["actions"][0]["action"]["value"]
        )
