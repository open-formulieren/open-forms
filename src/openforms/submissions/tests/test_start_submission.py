"""
Tests for the start of a submission.

A submission acts sort of like a session. It is tied to a particular form (which is made
up of form steps with their definitions).

Functional requirements are:

* multiple submissions for the same flow must be able to exist at the same time
* data of different submissions should not affect each other
* "login" makes no sense, as we are usually dealing with anonymous users
"""
from django.test import override_settings

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ...authentication.constants import AuthAttribute
from ..constants import SUBMISSIONS_SESSION_KEY
from ..models import Submission


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class SubmissionStartTests(APITestCase):
    endpoint = reverse_lazy("api:submission-list")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # ensure there is a form definition
        cls.form = FormFactory.create()
        cls.step = FormStepFactory.create(form=cls.form)
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def test_start_submission(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body, HTTP_HOST="testserver.com")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get()
        submission_step_url = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": self.step.uuid},
        )

        response_json = response.json()
        expected = {
            "id": str(submission.uuid),
            "form": f"http://testserver.com{self.form_url}",
            "nextStep": f"http://testserver.com{submission_step_url}",
        }
        for key, value in expected.items():
            with self.subTest(key=key, value=value):
                self.assertIn(key, response_json)
                self.assertEqual(response_json[key], value)

        # check that the submission ID is in the session
        self.assertEqual(
            response.wsgi_request.session[SUBMISSIONS_SESSION_KEY],
            [str(submission.uuid)],
        )

    def test_start_second_submission(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        with self.subTest(state="first submission"):
            response = self.client.post(self.endpoint, body)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        with self.subTest(state="second submission"):
            response = self.client.post(self.endpoint, body)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            submissions = Submission.objects.all()
            self.assertEqual(submissions.count(), 2)

            ids = submissions.values_list("uuid", flat=True)
            self.assertEqual(
                set(response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]),
                {str(uuid) for uuid in ids},
            )

    def test_start_submission_bsn_in_session(self):
        session = self.client.session
        session["form_auth"] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
        }
        session.save()

        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission = Submission.objects.get()
        self.assertEqual(submission.bsn, "123456782")
        self.assertEqual(submission.auth_plugin, "digid")

    def test_start_submission_in_maintenance_mode(self):
        form = FormFactory.create(maintenance_mode=True)
        step = FormStepFactory.create(form=form)

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_start_submission_blank_form_url(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_start_submission_bad_form_url(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://badserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
