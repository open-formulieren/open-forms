"""
Assert that (submission) variables are injected at key stages.

The formio dynamic configuration must interpolate variables using the supported
expressions. Most notably, this is relevant for the:

* GET submission step detail endpoint
* POST evaluate logic check endpoint
"""

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.formio.tests.assertions import FormioMixin
from openforms.forms.tests.factories import FormFactory, FormVariableFactory
from openforms.variables.constants import FormVariableDataTypes

from ..factories import SubmissionStepFactory
from ..mixins import SubmissionsMixin

CONFIGURATION = {
    "components": [
        {
            "type": "fieldset",
            "key": "group1",
            "label": "{{ labels.group1 }}",
            "components": [
                {
                    "type": "textfield",
                    "key": "text1",
                    "label": "{{ labels.text1 }}",
                    "description": "{{ helpTexts.text1 }}",
                }
            ],
        },
        {
            "type": "checkbox",
            "key": "checkbox1",
            "label": "Enable {{ text1|default:'' }}?",
            "defaultValue": False,
            "hidden": True,
        },
        {
            "type": "content",
            "key": "content1",
            "html": "<p>{{ text1|default:'' }} enabled: {{ checkbox1|yesno:'yes,no' }}</p>",
        },
    ]
}


class VariableInjectionTests(SubmissionsMixin, FormioMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration=CONFIGURATION,
        )
        form_step = form.formstep_set.get()
        FormVariableFactory.create(
            user_defined=True,
            form=form,
            key="labels",
            data_type=FormVariableDataTypes.object,
            initial_value={
                "group1": "Group 1",
                "text1": "Label 1",
            },
        )
        FormVariableFactory.create(
            user_defined=True,
            form=form,
            key="helpTexts",
            data_type=FormVariableDataTypes.object,
            initial_value={
                "text1": "Help 1",
            },
        )
        submission_step = SubmissionStepFactory.create(
            submission__form=form, form_step=form_step, data={}
        )

        cls.submission_step = submission_step
        cls.submission = submission_step.submission

    def test_detail_endpoint_interpolates_variables(self):
        self._add_submission_to_session(self.submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.submission_step.form_step.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        configuration = response.json()["formStep"]["configuration"]

        with self.subTest(component="group1"):
            self.assertFormioComponent(
                configuration,
                "group1",
                {"label": "Group 1"},
            )
        with self.subTest(component="text1"):
            self.assertFormioComponent(
                configuration,
                "text1",
                {
                    "label": "Label 1",
                    "description": "Help 1",
                },
            )
        with self.subTest(component="checkbox1"):
            self.assertFormioComponent(
                configuration,
                "checkbox1",
                {
                    "label": "Enable ?",  # empty variable -> empty string
                },
            )
        with self.subTest(component="content1"):
            self.assertFormioComponent(
                configuration,
                "content1",
                {"html": "<p> enabled: no</p>"},
            )

    def test_detail_endpoint_interpolates_with_submission_data(self):
        self._add_submission_to_session(self.submission)
        self.submission_step.data = {"text1": 'First "textfield"', "checkbox1": True}
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.submission_step.form_step.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        configuration = response.json()["formStep"]["configuration"]

        with self.subTest(component="group1"):
            self.assertFormioComponent(
                configuration,
                "group1",
                {"label": "Group 1"},
            )
        with self.subTest(component="text1"):
            self.assertFormioComponent(
                configuration,
                "text1",
                {
                    "label": "Label 1",
                    "description": "Help 1",
                },
            )
        with self.subTest(component="checkbox1"):
            self.assertFormioComponent(
                configuration,
                "checkbox1",
                {
                    "label": "Enable First &quot;textfield&quot;?",
                },
            )
        with self.subTest(component="content1"):
            self.assertFormioComponent(
                configuration,
                "content1",
                {"html": "<p>First &quot;textfield&quot; enabled: yes</p>"},
            )

    def test_logic_evalution_endpoint(self):
        self._add_submission_to_session(self.submission)
        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.submission_step.form_step.uuid,
            },
        )

        response = self.client.post(endpoint, {"data": {"text1": "some input"}})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        configuration = response.json()["step"]["formStep"]["configuration"]

        with self.subTest(component="group1"):
            self.assertFormioComponent(
                configuration,
                "group1",
                {"label": "Group 1"},
            )
        with self.subTest(component="text1"):
            self.assertFormioComponent(
                configuration,
                "text1",
                {
                    "label": "Label 1",
                    "description": "Help 1",
                },
            )
        with self.subTest(component="checkbox1"):
            self.assertFormioComponent(
                configuration,
                "checkbox1",
                {
                    "label": "Enable some input?",
                },
            )
        with self.subTest(component="content1"):
            self.assertFormioComponent(
                configuration,
                "content1",
                {"html": "<p>some input enabled: no</p>"},
            )
