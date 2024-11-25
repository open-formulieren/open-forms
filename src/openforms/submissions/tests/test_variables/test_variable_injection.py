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

from ..factories import SubmissionFactory, SubmissionStepFactory
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


class VariableInjectionI18NTests(SubmissionsMixin, FormioMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.submission = SubmissionFactory.from_components(
            language_code="en",
            components_list=[
                {
                    "key": "naam",
                    "type": "textfield",
                    "label": "Naam",
                    "openForms": {
                        "translations": {
                            "en": {"label": "Name"},
                            "nl": {"label": "Naam"},
                        }
                    },
                },
                {
                    "key": "geboortedatum",
                    "type": "date",
                    "label": "Geboortedatum",
                    "format": "dd-MM-yyyy",
                    "openForms": {
                        "translations": {
                            "en": {"label": "Birthdate"},
                            "nl": {"label": "Geboortedatum"},
                        }
                    },
                },
                {
                    "key": "ww",
                    "type": "textfield",
                    "label": "Wachtwoord",
                    "description": 'Suggestie: #{{naam|title}}{{geboortedatum|date:"Y"}}',
                    "openForms": {
                        "translations": {
                            "en": {
                                "description": "Suggestion: #{{naam|title}}{{geboortedatum|date:'Y'}}"
                            },
                            "nl": {
                                "description": "Suggestie: #{{naam|title}}{{geboortedatum|date:'Y'}}"
                            },
                        }
                    },
                },
                {
                    "key": "ww_check",
                    "type": "checkbox",
                    "label": "Bevestig uw wachtwoord: {{ww}}",
                    "description": "Mooi hè? We laten u niet 2 maal hetzelfde "
                    "typen. Gemak > veiligheid.",
                    "openForms": {
                        "translations": {
                            "en": {
                                "label": "Confirm your password: {{ww}}",
                                "description": "Nice, eh? We won't make you type the same thing twice. Convenience over safety.",
                            },
                            "nl": {
                                "label": "Bevestig uw wachtwoord: {{ww}}",
                                "description": "Mooi hè? We laten u niet 2 maal hetzelfde typen. Gemak > veiligheid.",
                            },
                        }
                    },
                },
            ],
            submitted_data={
                "naam": "Alice",
                "geboortedatum": "1865-01-01",
                "ww": "L3GyL4V5Maus2Jg",
            },
        )
        cls.form_step = cls.submission.steps[0].form_step
        cls.form_step.form_definition.save()

    def test_variable_interpolates_on_translated_definitions(self):
        self._add_submission_to_session(self.submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.form_step.uuid,
            },
        )

        step_json = self.client.get(endpoint).json()
        components_by_key = {
            c["key"]: c for c in step_json["formStep"]["configuration"]["components"]
        }

        c = components_by_key.get

        self.assertEqual(c("naam")["label"], "Name")
        self.assertEqual(c("geboortedatum")["label"], "Birthdate")
        self.assertEqual(c("ww")["label"], "Wachtwoord")  # no translation provided
        self.assertEqual(c("ww")["description"], "Suggestion: #Alice1865")
        self.assertEqual(
            c("ww_check")["label"], "Confirm your password: L3GyL4V5Maus2Jg"
        )
        self.assertEqual(
            c("ww_check")["description"],
            "Nice, eh? We won't make you type the same thing twice. Convenience over safety.",
        )

    def test_interpolates_dirty_data_on_translated_definitions(self):
        self._add_submission_to_session(self.submission)

        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.form_step.uuid,
            },
        )

        check_json = self.client.post(
            endpoint,
            {
                "data": {
                    "naam": "Bob",
                    "geboortedatum": "1999-05-01",
                    "ww": "PatrickBFF",
                }
            },
        ).json()

        components_by_key = {
            c["key"]: c
            for c in check_json["step"]["formStep"]["configuration"]["components"]
        }

        c = components_by_key.get

        self.assertEqual(c("naam")["label"], "Name")
        self.assertEqual(c("geboortedatum")["label"], "Birthdate")
        self.assertEqual(c("ww")["label"], "Wachtwoord")  # no translation provided
        self.assertEqual(c("ww")["description"], "Suggestion: #Bob1999")
        self.assertEqual(c("ww_check")["label"], "Confirm your password: PatrickBFF")
        self.assertEqual(
            c("ww_check")["description"],
            "Nice, eh? We won't make you type the same thing twice. Convenience over safety.",
        )
