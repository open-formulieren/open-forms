"""
Tests for various authentication modes for a given form.

From security issue #16 / security advisory GHSA-g936-w68m-87j8 - if authentication on
the form is required, the API endpoints must respond with HTTP 403 when the end-user
did not authenticate. This applies to:

- starting a submission
- submitting step data of a submission step

If authentication is optional, then this behaviour does not apply.
"""

from unittest.mock import patch

from django.test import override_settings, tag

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory

from ..models import Submission
from .factories import SubmissionFactory
from .mixins import SubmissionsMixin


@tag("GHSA-g936-w68m-87j8")
@override_settings(ALLOWED_HOSTS=["testserver", "testserver.com"])
class AuthOptionalTests(SubmissionsMixin, APITestCase):
    endpoint = reverse_lazy("api:submission-list")

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.form = FormFactory.create(
            generate_minimal_setup=True,
            authentication_backend="demo",
            formstep__form_definition__login_required=False,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "component1",
                        "label": "component1",
                    }
                ]
            },
        )
        assert cls.form.login_required is False, "Authentication should be optional"
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    @patch("openforms.submissions.api.viewsets.submission_start.send", autospec=True)
    def test_start_submission_is_allowed(self, mock_signal):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
            "anonymous": True,
        }

        response = self.client.post(self.endpoint, body, HTTP_HOST="testserver.com")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_signal.assert_called_once()
        self.assertEqual(mock_signal.call_args_list[0].kwargs["anonymous"], True)

    def test_submitting_step_data_is_allowed_anon_user(self):
        submission = SubmissionFactory.create(form=self.form)
        assert not submission.is_authenticated, "Submission must be anonymous"
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": self.form.formstep_set.get().uuid,
            },
        )
        body = {"data": {"component1": "henlo"}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_submitting_step_data_is_allowed_authenticated_user(self):
        submission = SubmissionFactory.create(
            form=self.form,
            auth_info__plugin=self.form.auth_backends.get().backend,
            auth_info__value="123456782",
        )
        assert submission.is_authenticated, "Submission must have auth details"
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": self.form.formstep_set.get().uuid,
            },
        )
        body = {"data": {"component1": "henlo"}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


@tag("GHSA-g936-w68m-87j8")
@override_settings(ALLOWED_HOSTS=["testserver", "testserver.com"])
class AuthRequiredTests(SubmissionsMixin, APITestCase):
    endpoint = reverse_lazy("api:submission-list")

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.form = FormFactory.create(
            generate_minimal_setup=True,
            authentication_backend="demo",
            formstep__form_definition__login_required=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "component1",
                        "label": "component1",
                    }
                ]
            },
        )
        assert cls.form.login_required is True, "Authentication should be required"
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def test_start_submission_is_not_allowed(self):
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(self.endpoint, body, HTTP_HOST="testserver.com")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Submission.objects.exists())

    def test_submitting_step_data_is_not_allowed_anon_user(self):
        submission = SubmissionFactory.create(form=self.form)
        assert not submission.is_authenticated, "Submission must be anonymous"
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": self.form.formstep_set.get().uuid,
            },
        )
        body = {"data": {"component1": "henlo"}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_submitting_step_data_is_allowed_authenticated_user(self):
        submission = SubmissionFactory.create(
            form=self.form,
            auth_info__plugin=self.form.auth_backends.get().backend,
            auth_info__value="123456782",
        )
        assert submission.is_authenticated, "Submission must have auth details"
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": self.form.formstep_set.get().uuid,
            },
        )
        body = {"data": {"component1": "henlo"}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
