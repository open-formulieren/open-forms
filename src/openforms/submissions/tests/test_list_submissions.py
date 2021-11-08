"""
The list endpoint makes it possible to resume submissions that were started,
based on the session cookie. It is not possible to list submissions on different
devices.

In the future, it could be possible to retrieve submissions as well based on BSN after
DigiD login (or comparable).
"""
from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory

from .factories import SubmissionFactory
from .mixins import SubmissionsMixin


class SubmissionListTests(SubmissionsMixin, APITestCase):
    maxDiff = None
    endpoint = reverse_lazy("api:submission-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # ensure there is a form definition
        cls.form = FormFactory.create()
        cls.step = FormStepFactory.create(
            form=cls.form, form_definition__name="Select product"
        )

    def test_list_own_submissions(self):
        [sub1, sub2, sub3] = SubmissionFactory.create_batch(3, form=self.form)
        for submission in [sub1, sub3]:
            self._add_submission_to_session(submission)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        # paginated response
        self.assertIn("results", response_data)
        self.assertEqual(response_data["count"], 2)
        ids = [res["id"] for res in response_data["results"]]
        self.assertEqual(set(ids), {str(sub1.uuid), str(sub3.uuid)})

    def test_list_response_format(self):
        submission = SubmissionFactory.create(
            form=self.form, form_url="http://formserver/myform"
        )
        self._add_submission_to_session(submission)
        submission_path = reverse(
            "api:submission-detail", kwargs={"uuid": submission.uuid}
        )
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": self.form.uuid})
        form_step_path = reverse(
            "api:form-steps-detail",
            kwargs={
                "form_uuid_or_slug": self.form.uuid,
                "uuid": self.step.uuid,
            },
        )
        submission_step_path = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": self.step.uuid,
            },
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {
            "id": str(submission.uuid),
            "url": f"http://testserver{submission_path}",
            "form": f"http://testserver{form_path}",
            "formUrl": "http://formserver/myform",
            "steps": [
                {
                    "id": str(self.step.uuid),
                    "url": f"http://testserver{submission_step_path}",
                    "formStep": f"http://testserver{form_step_path}",
                    "isApplicable": True,
                    "completed": False,
                    "optional": False,
                    "name": "Select product",
                    "canSubmit": True,
                }
            ],
            "nextStep": f"http://testserver{submission_step_path}",
            "canSubmit": True,
            "payment": {
                "isRequired": False,
                "hasPaid": False,
                "amount": "15.00",
            },
        }

        self.assertEqual(
            response.json()["results"],
            [expected],
        )
