"""
Tests for the start of a submission.

A submission acts sort of like a session. It is tied to a particular form (which is made
up of form steps with their definitions).

Functional requirements are:

* multiple submissions for the same flow must be able to exist at the same time
* data of different submissions should not affect each other
* "login" usually is not releavnt, as we mostly deal with anonymous users. However,
  some plugins/functionality is limited to staff users.

See ``test_disabled_forms.py`` for more extensive tests around maintenance mode.
"""

from django.test import override_settings, tag

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.authentication.service import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.forms.tests.factories import (
    FormFactory,
    FormStepFactory,
    FormVariableFactory,
)

from ..constants import SUBMISSIONS_SESSION_KEY, SubmissionValueVariableSources
from ..models import Submission, SubmissionValueVariable


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
    TIMELINE_HANDLER_DISABLED=True,
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

        response_json = response.json()
        expected = {
            "id": str(submission.uuid),
            "form": f"http://testserver.com{self.form_url}",
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
        session[FORM_AUTH_SESSION_KEY] = {
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
        self.assertEqual(submission.auth_info.value, "123456782")
        self.assertEqual(submission.auth_info.plugin, "digid")

        # Auth info should be removed from session after the submission is started
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)

    @tag("gh-4199")
    def test_two_submissions_within_same_session(self):
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
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
        self.assertEqual(submission.auth_info.value, "123456782")
        self.assertEqual(submission.auth_info.plugin, "digid")

        # Auth info should be removed from session after the submission is started
        self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)

        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
            "anonymous": True,
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        submission = Submission.objects.last()
        with self.assertRaises(Submission.auth_info.RelatedObjectDoesNotExist):
            submission.auth_info

    def test_start_submission_on_deleted_form(self):
        form = FormFactory.create(deleted_=True)
        FormStepFactory.create(form=form)

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

    def test_start_submission_with_prefill(self):
        FormVariableFactory.create(
            form=self.form,
            form_definition=self.step.form_definition,
            prefill_plugin="demo",
            prefill_attribute="random_string",
        )
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body, HTTP_HOST="testserver.com")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        submission = Submission.objects.get()
        submission_variables = SubmissionValueVariable.objects.filter(
            submission=submission
        )

        self.assertEqual(1, submission_variables.count())

        prefilled_variable = submission_variables.get()

        self.assertTrue(prefilled_variable.value != "")
        self.assertEqual(
            SubmissionValueVariableSources.prefill, prefilled_variable.source
        )

    def test_start_submission_with_initial_data_reference(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
            "initialDataReference": "of-or-3452fre3",
        }

        response = self.client.post(self.endpoint, body)

        submission = Submission.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            submission.initial_data_reference, body["initialDataReference"]
        )

    def test_start_submission_with_form_max_submissions_limit_not_reached(self):
        form = FormFactory.create(submission_limit=1)
        FormStepFactory.create(form=form)

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_start_submission_with_form_max_submissions_limit_reached(self):
        form = FormFactory.create(submission_limit=1, submission_counter=1)
        FormStepFactory.create(form=form)

        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        body = {
            "form": f"http://testserver.com{form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
