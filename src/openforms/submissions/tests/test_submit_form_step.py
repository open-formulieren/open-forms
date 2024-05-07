"""
Test submitting a single form step in a submission.

When a submission ("session") is started, the data for a single form step must be
submitted to a submission step. Existing data can be overwritten and new data is created
by using HTTP PUT.
"""

from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

from ..models import SubmissionValueVariable
from .factories import SubmissionFactory, SubmissionStepFactory
from .mixins import SubmissionsMixin


@temp_private_root()
class FormStepSubmissionTests(SubmissionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # ensure there is a form definition
        cls.form = FormFactory.create()
        cls.step1 = FormStepFactory.create(
            form=cls.form,
            form_definition__configuration={
                "components": [{"key": "test-key", "type": "textfield"}]
            },
        )

        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

        # ensure there is a submission
        cls.submission = SubmissionFactory.create(form=cls.form)

    @freeze_time("2022-05-25T10:53:19+00:00")
    def test_create_step_data(self):
        self._add_submission_to_session(self.submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.step1.uuid,
            },
        )
        body = {"data": {"test-key": "example data"}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission_step = self.submission.submissionstep_set.get()
        self.assertEqual(
            response.json(),
            {
                "id": str(submission_step.uuid),
                "slug": self.step1.slug,
                "formStep": {
                    "index": 0,
                    "configuration": {
                        "components": [{"type": "textfield", "key": "test-key"}]
                    },
                },
                "data": {
                    "test-key": "example data",
                },
                "isApplicable": True,
                "completed": True,
                "canSubmit": True,
            },
        )
        self.assertEqual(submission_step.data, {"test-key": "example data"})

        submission_variables = SubmissionValueVariable.objects.filter(
            submission=self.submission
        )

        self.assertEqual(1, submission_variables.count())

        variable = submission_variables.get()

        self.assertEqual("test-key", variable.key)
        self.assertEqual("example data", variable.value)
        self.assertEqual("2022-05-25T10:53:19+00:00", variable.created_at.isoformat())

    def test_create_step_wrong_step_id(self):
        """
        Validate that the step UUID belongs to the submission form.
        """
        other_form_step = FormStepFactory.create()
        assert other_form_step.form != self.form
        self._add_submission_to_session(self.submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": other_form_step.uuid,
            },
        )

        response = self.client.put(endpoint, {})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_step_invalid_submission_id(self):
        """
        Validate that the user must "own" the submission.
        """
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.step1.uuid,
            },
        )

        response = self.client.put(endpoint, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_step_data(self):
        self._add_submission_to_session(self.submission)

        step2 = FormStepFactory.create(
            form=self.form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "foo",
                    },
                    {
                        "type": "textfield",
                        "key": "modified",
                    },
                ]
            },
        )

        SubmissionStepFactory.create(
            submission=self.submission,
            form_step=self.step1,
        )
        submission_step = SubmissionStepFactory.create(
            submission=self.submission,
            data={"foo": "bar"},
            form_step=step2,
        )

        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": self.submission.uuid,
                "step_uuid": step2.uuid,
            },
        )
        body = {"data": {"modified": "data"}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "id": str(submission_step.uuid),
                "slug": step2.slug,
                "formStep": {
                    "index": 1,
                    "configuration": {
                        "components": [
                            {"key": "foo", "type": "textfield"},
                            {"key": "modified", "type": "textfield"},
                        ]
                    },
                },
                "data": {
                    "foo": "bar",
                    "modified": "data",
                },
                "isApplicable": True,
                "completed": True,
                "canSubmit": True,
            },
        )
        submission_step.refresh_from_db()
        self.assertEqual(submission_step.data, {"modified": "data"})

        submission_variables = SubmissionValueVariable.objects.filter(
            submission=self.submission
        )

        # The submission variable for 'foo' has been deleted
        self.assertEqual(1, submission_variables.count())

        submission_variable = submission_variables.get(key="modified")

        self.assertEqual("data", submission_variable.value)

    def test_data_not_underscored(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "countryOfResidence",  # CamelCase
                        "type": "textfield",
                        "label": "Country of residence",
                    }
                ]
            }
        )
        form_step = FormStepFactory.create(form_definition=form_definition)

        submission = SubmissionFactory.create(form=form_step.form)
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )
        body = {"data": {"countryOfResidence": "Netherlands"}}

        response = self.client.put(endpoint, body)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        saved_data = submission.submissionstep_set.get().data

        # Check that the data has not been converted to snake case
        self.assertIn("countryOfResidence", saved_data)
        self.assertNotIn("country_of_residence", saved_data)

    def test_data_not_camelised(self):
        form_definition = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "country_of_residence",  # Snake Case
                        "type": "textfield",
                        "label": "Country of residence",
                    }
                ]
            }
        )
        form_step = FormStepFactory.create(form_definition=form_definition)
        submission = SubmissionFactory.create(form=form_step.form)
        SubmissionStepFactory.create(
            submission=submission,
            data={"country_of_residence": "Netherlands"},
            form_step=form_step,
        )
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form_step.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]
        # Check that the data has not been converted to camel case
        self.assertIn("country_of_residence", data)
        self.assertNotIn("countryOfResidence", data)
