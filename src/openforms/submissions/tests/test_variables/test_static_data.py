from django.test import override_settings

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)
from openforms.variables.constants import FormVariableSources

from ...models import Submission
from ..factories import SubmissionFactory
from ..mixins import SubmissionsMixin


@override_settings(CORS_ALLOW_ALL_ORIGINS=True)
class StaticVariablesTests(SubmissionsMixin, APITestCase):
    def test_start_submission(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "key": "content",
                        "html": "<p>The raw time now is: {{ now.isoformat }}</p>",
                        "type": "content",
                        "label": "Content",
                    },
                ]
            },
        )
        FormVariableFactory.create(form=form, source=FormVariableSources.user_defined)

        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        start_endpoint = reverse("api:submission-list")
        body = {
            "form": f"http://testserver.com{form_path}",
            "formUrl": "http://testserver.com/my-form",
        }
        # start a submission
        response = self.client.post(start_endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        submission = Submission.objects.get()
        submission_variables = submission.submissionvaluevariable_set.all()

        # Only the user defined variable is initiated after creating the submission
        self.assertEqual(1, submission_variables.count())

        submission_step_endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )
        with freeze_time("2021-07-29T14:00:00Z"):
            response = self.client.get(submission_step_endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        content_field = response_data["formStep"]["configuration"]["components"][0][
            "html"
        ]
        data = response_data["data"]

        # The static variable is used in the dynamic configuration ...
        self.assertIn("The raw time now is: 2021-07-29T14:00:00+00:00", content_field)
        # ... but it is not sent back in the data
        self.assertEqual({}, data)

    def test_check_logic(self):
        form = FormFactory.create()
        form_step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                        "label": "name",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            key="isJohn",
            source=FormVariableSources.user_defined,
            initial_value=False,
        )

        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "name"}, "John"]},
            actions=[
                {
                    "variable": "isJohn",
                    "action": {
                        "name": "Update variable",
                        "type": "variable",
                        "value": {"!!": ["0"]},  # Evaluates to True
                    },
                }
            ],
        )
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )

        response = self.client.post(endpoint, data={"data": {"name": "John"}})

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(
            # Only changed data is returned and static variables are not present in the data
            {},
            response.data["step"]["data"],
        )

    def test_save_step_doesnt_save_static_variables(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                        "label": "name",
                    },
                ]
            },
        )

        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)

        submission_step_endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": form.formstep_set.get().uuid,
            },
        )
        response = self.client.put(
            submission_step_endpoint, data={"data": {"name": "John"}}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(1, submission.submissionvaluevariable_set.count())
        self.assertEqual("name", submission.submissionvaluevariable_set.get().key)
