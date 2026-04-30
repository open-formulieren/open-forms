from unittest.mock import MagicMock, patch

from django.test import override_settings

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory

from ..models import Submission

# TODO
# Update tests when the frontend part has been merged (would be nice to have e2e tests too)


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class SingleStepFormTests(APITestCase):
    @patch("openforms.submissions.api.viewsets.prefill_variables")
    def test_single_step_form_flow(self, m: MagicMock):
        endpoint = reverse_lazy("api:submission-list")
        form = FormFactory.create(generate_minimal_setup=True, is_single_step_form=True)
        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})

        # 1. create the submission
        submission_body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
            "anonymous": True,
            "initialDataReference": "of-or-3452fre3",
        }

        submission_response = self.client.post(
            endpoint, submission_body, HTTP_HOST="testserver.com"
        )
        submission = Submission.objects.get()
        form_step = form.formstep_set.get()

        self.assertEqual(submission_response.status_code, status.HTTP_201_CREATED)

        # 2. validate step data
        validate_endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        validate_data = {"test-key-0": "foo"}
        validate_data_response = self.client.post(
            validate_endpoint, validate_data, HTTP_HOST="testserver.com"
        )

        self.assertEqual(validate_data_response.status_code, status.HTTP_204_NO_CONTENT)

        # 3. submit step data
        submit_data_endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": form_step.uuid},
        )
        submit_data = {"data": {"test-key-0": "foo"}}
        submit_data_response = self.client.put(
            submit_data_endpoint, submit_data, HTTP_HOST="testserver.com"
        )

        self.assertEqual(submit_data_response.status_code, status.HTTP_201_CREATED)

        # 4. complete form
        complete_submission_endpoint = reverse(
            "api:submission-complete",
            kwargs={"uuid": submission.uuid},
        )
        complete_data = {
            "privacy_policy_accepted": True,
            "statementOfTruthAccepted": False,
        }
        complete_submission_response = self.client.post(
            complete_submission_endpoint, complete_data, HTTP_HOST="testserver.com"
        )

        self.assertEqual(complete_submission_response.status_code, status.HTTP_200_OK)

        # 5. make sure the prefill was not called
        m.assert_not_called()
