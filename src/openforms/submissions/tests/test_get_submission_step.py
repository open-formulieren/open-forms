"""
Relates to issue #110

A form and its form step definitions are a static declaration, which can include
custom field types. The custom field types only resolve within the context of a
submission to be able to be transformed into vanilla Formio definitions.

The tests in this module validate that we can retrieve the submission-context
aware step definition.
"""
import json
import uuid

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.core.custom_field_types import register, unregister
from openforms.core.tests.factories import FormStepFactory

from .factories import SubmissionFactory
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
                    "type": "textfield",
                },
                {
                    "label": "Other field",
                    "type": "selectboxes",
                    "inputType": "checkbox",
                },
            ]
        }
        # FIXME: the json.dumps should _not_ be needed with JSONField
        cls.step = FormStepFactory.create(
            form_definition__configuration=json.dumps(configuration)
        )
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
            "formStep": {
                "index": 0,
                "configuration": {
                    "components": [
                        {
                            "label": "Some field",
                            "type": "textfield",
                        },
                        {
                            "label": "Other field",
                            "type": "selectboxes",
                            "inputType": "checkbox",
                        },
                    ]
                },
            },
            "data": None,
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
            "formStep": {
                "index": 0,
                "configuration": {
                    "components": [
                        {
                            "label": "Rewritten label",
                            "type": "textfield",
                        },
                        {
                            "label": "Other field",
                            "type": "selectboxes",
                            "inputType": "checkbox",
                        },
                    ]
                },
            },
            "data": None,
        }
        self.assertEqual(response.json(), expected)

    def test_invalid_submission_id(self):
        self._add_submission_to_session(self.submission)
        self.submission.delete()

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
