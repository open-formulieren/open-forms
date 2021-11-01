"""
All state is managed on the backend - it's the definitive source of truth which also
makes resuming possible across devices (if you have a "magic link").

This information drives the frontend/navigation.
"""

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.logging.models import TimelineLogProxy

from .factories import SubmissionFactory
from .mixins import SubmissionsMixin


class SubmissionReadTests(SubmissionsMixin, APITestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # ensure there is a form definition
        cls.form = FormFactory.create()
        cls.step = FormStepFactory.create(
            form=cls.form, form_definition__name="Select product"
        )
        cls.submission = SubmissionFactory.create(form=cls.form)
        cls.endpoint = reverse(
            "api:submission-detail", kwargs={"uuid": cls.submission.uuid}
        )

    def test_invalid_submission_id(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_details_view_api.txt"
            ).exists()
        )

    def test_retrieve_submission_nothing_submitted(self):
        self._add_submission_to_session(self.submission)
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
                "submission_uuid": self.submission.uuid,
                "step_uuid": self.step.uuid,
            },
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            {
                "id": str(self.submission.uuid),
                "url": f"http://testserver{self.endpoint}",
                "form": f"http://testserver{form_path}",
                "formUrl": "",
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
            },
        )
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_details_view_api.txt"
            ).count(),
            1,
        )

    def test_retrieve_submission_optional_steps(self):
        self._add_submission_to_session(self.submission)
        self.step.optional = True
        self.step.save()

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        step = response.json()["steps"][0]
        self.assertTrue(step["optional"])
        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_details_view_api.txt"
            ).count(),
            1,
        )
