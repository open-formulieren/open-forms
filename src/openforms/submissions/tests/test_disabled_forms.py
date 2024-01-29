"""
Forms can be disabled in one of two ways:

* active=False -> the form is disabled for everyone, including admin users
* maintenance=True -> the form is disabled for regular users, but admin users can still
  use the form

Maintenance mode is communicated using HTTP 503 - it's temporarily unavailable.

De-activated is communicated using HTTP 422 (Unprocessable Entity) - the client did not
expect the form to be deactivated. See also https://stackoverflow.com/a/62450708
Other contenders are HTTP 409 (conflict) and HTTP 410 (Gone), but the client cannot
resolve the 409, and it's not the submission/step resource itself that's gone, but
the form it belongs to.
"""

from unittest.mock import patch

from django.test import override_settings, tag

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.authentication.tests.factories import AuthInfoFactory
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission

from ..tokens import submission_resume_token_generator
from .factories import SubmissionFactory, SubmissionStepFactory
from .mixins import SubmissionsMixin


@tag("gh-1967")
@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class InactiveFormTests(SubmissionsMixin, APITestCase):
    """
    Tests for forms that are not active.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.form = FormFactory.create(generate_minimal_setup=True, active=False)
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def _assert_submission_removed_from_session(self, submission: Submission):
        with self.subTest("submission removed from session"):
            endpoint = reverse(
                "api:submission-detail", kwargs={"uuid": submission.uuid}
            )

            response = self.client.get(endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_form_detail(self):
        form_detail = self.client.get(self.form_url)

        self.assertEqual(form_detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_start_submission(self):
        submissions_url = reverse("api:submission-list")
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(submissions_url, body)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        error = response.json()
        self.assertEqual(error["code"], "form-inactive")

    def test_cannot_validate_step_data(self):
        """
        Assert that step data validation returns HTTP 422 for deactivated forms.

        This shortcuts and improves user experience - if the step data is invalid,
        there's no point in providing that feedback and having the user correct the
        mistakes if the next action (submit) just leads to another error that the form
        is no longer available.
        """
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        body = {"data": {}}

        response = self.client.post(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        error = response.json()
        self.assertEqual(error["code"], "form-inactive")
        self._assert_submission_removed_from_session(submission)

    def test_cannot_logic_check_step_data(self):
        """
        Assert that step data logic check returns HTTP 422 for deactivated forms.

        This shortcuts and improves user experience - if the step data is invalid,
        there's no point in providing that feedback and having the user correct the
        mistakes if the next action (submit) just leads to another error that the form
        is no longer available.
        """
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        body = {"data": {}}

        response = self.client.post(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        error = response.json()
        self.assertEqual(error["code"], "form-inactive")
        self._assert_submission_removed_from_session(submission)

    def test_cannot_submit_step_data(self):
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        body = {"data": {}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        error = response.json()
        self.assertEqual(error["code"], "form-inactive")
        self._assert_submission_removed_from_session(submission)

    def test_cannot_complete_submission(self):
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        SubmissionStepFactory.create(submission=submission, form_step=step, data={})
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        error = response.json()
        self.assertEqual(error["code"], "form-inactive")
        self._assert_submission_removed_from_session(submission)

    def test_cannot_suspend_submission(self):
        submission = SubmissionFactory.create(form=self.form)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"email": "foo@bar.com"})

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        error = response.json()
        self.assertEqual(error["code"], "form-inactive")
        self._assert_submission_removed_from_session(submission)

    def test_resume_submission(self):
        """
        Test that resuming a form that has been deactivated is not possible.

        It's possible a submission is suspended while the form is still active,
        but time passes and by the time the submission is resumed, the form has been
        deactivated.

        The resume page should then display an error instead of redirecting to the
        UI/frontend.
        """
        submission = SubmissionFactory.create(form=self.form)
        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        # _not_ 301/302/30x redirect
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "submissions/resume_form_error.html")
        self._assert_submission_removed_from_session(submission)

    @patch("openforms.authentication.models.hash_identifying_attributes_task")
    def test_submission_auth_attributes_hashed(self, mock_hash_task):
        submission = SubmissionFactory.create(form=self.form)
        AuthInfoFactory.create(submission=submission, value="123456782")
        step = self.form.formstep_set.get()
        SubmissionStepFactory.create(submission=submission, form_step=step, data={})
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        mock_hash_task.delay.assert_called_once_with(submission.auth_info.id)


class InactiveFormAuthenticatedUserTests(InactiveFormTests):
    """
    Identical tests, but with an authenticated non-staff user.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create()

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)


class InactiveFormStaffUserTests(InactiveFormTests):
    """
    Identical tests, but with an authenticated non-staff user.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = StaffUserFactory.create()

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_form_detail(self):
        form_detail = self.client.get(self.form_url)

        self.assertEqual(form_detail.status_code, status.HTTP_200_OK)


@tag("gh-1967")
@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class MaintenanceFormAnonUserTests(SubmissionsMixin, APITestCase):
    """
    Tests for forms in maintenance mode.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.form = FormFactory.create(
            generate_minimal_setup=True, active=True, maintenance_mode=True
        )
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def test_retrieve_form_detail(self):
        form_detail = self.client.get(self.form_url)

        self.assertEqual(form_detail.status_code, status.HTTP_200_OK)

    def test_cannot_start_submission(self):
        submissions_url = reverse("api:submission-list")
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(submissions_url, body)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = response.json()["invalidParams"][0]
        self.assertEqual(error["name"], "form")
        self.assertEqual(error["code"], "form-maintenance")

    def test_cannot_validate_step_data(self):
        """
        Assert that step data validation returns HTTP 422 for deactivated forms.

        This shortcuts and improves user experience - if the step data is invalid,
        there's no point in providing that feedback and having the user correct the
        mistakes if the next action (submit) just leads to another error that the form
        is no longer available.
        """
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        body = {"data": {}}

        response = self.client.post(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        error = response.json()
        self.assertEqual(error["code"], "form-maintenance")

    def test_cannot_logic_check_step_data(self):
        """
        Assert that step data logic check returns HTTP 422 for deactivated forms.

        This shortcuts and improves user experience - if the step data is invalid,
        there's no point in providing that feedback and having the user correct the
        mistakes if the next action (submit) just leads to another error that the form
        is no longer available.
        """
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        body = {"data": {}}

        response = self.client.post(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        error = response.json()
        self.assertEqual(error["code"], "form-maintenance")

    def test_cannot_submit_step_data(self):
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        body = {"data": {}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        error = response.json()
        self.assertEqual(error["code"], "form-maintenance")

    def test_cannot_complete_submission(self):
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        SubmissionStepFactory.create(submission=submission, form_step=step, data={})
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        error = response.json()
        self.assertEqual(error["code"], "form-maintenance")

    def test_cannot_suspend_submission(self):
        submission = SubmissionFactory.create(form=self.form)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"email": "foo@bar.com"})

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        error = response.json()
        self.assertEqual(error["code"], "form-maintenance")

    def test_resume_submission(self):
        """
        Test that resuming a form that has been deactivated is not possible.

        It's possible a submission is suspended while the form is still active,
        but time passes and by the time the submission is resumed, the form has been
        deactivated.

        The resume page should then display an error instead of redirecting to the
        UI/frontend.
        """
        submission = SubmissionFactory.create(form=self.form)
        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        # _not_ 301/302/30x redirect
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertTemplateUsed(response, "submissions/resume_form_error.html")


class MaintenanceFormAuthenticatedUserTests(MaintenanceFormAnonUserTests):
    """
    Authenticated but non-staff users get the same behaviour as anonymous users.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory.create()

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_resume_submission(self):
        self.client.force_login(user=self.user)
        super().test_resume_submission()


@tag("gh-1967")
@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    ALLOWED_HOSTS=["*"],
    CORS_ALLOWED_ORIGINS=["http://testserver.com"],
)
class MaintenanceFormStaffUserTests(SubmissionsMixin, APITestCase):
    """
    Tests for forms in maintenance mode.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = StaffUserFactory.create()
        cls.form = FormFactory.create(
            generate_minimal_setup=True, active=True, maintenance_mode=True
        )
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_form_detail(self):
        form_detail = self.client.get(self.form_url)

        self.assertEqual(form_detail.status_code, status.HTTP_200_OK)

    def test_can_start_submission(self):
        submissions_url = reverse("api:submission-list")
        body = {
            "form": f"http://testserver.com{self.form_url}",
            "formUrl": "http://testserver.com/my-form",
        }

        response = self.client.post(submissions_url, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_validate_step_data(self):
        """
        Assert that step data validation returns HTTP 422 for deactivated forms.

        This shortcuts and improves user experience - if the step data is invalid,
        there's no point in providing that feedback and having the user correct the
        mistakes if the next action (submit) just leads to another error that the form
        is no longer available.
        """
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-validate",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        body = {"data": {}}

        response = self.client.post(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_can_logic_check_step_data(self):
        """
        Assert that step data logic check returns HTTP 422 for deactivated forms.

        This shortcuts and improves user experience - if the step data is invalid,
        there's no point in providing that feedback and having the user correct the
        mistakes if the next action (submit) just leads to another error that the form
        is no longer available.
        """
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-logic-check",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        body = {"data": {}}

        response = self.client.post(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_submit_step_data(self):
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={"submission_uuid": submission.uuid, "step_uuid": step.uuid},
        )
        body = {"data": {}}

        response = self.client.put(endpoint, body)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_complete_submission(self):
        submission = SubmissionFactory.create(form=self.form)
        step = self.form.formstep_set.get()
        SubmissionStepFactory.create(submission=submission, form_step=step, data={})
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"privacy_policy_accepted": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_suspend_submission(self):
        submission = SubmissionFactory.create(form=self.form)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"email": "foo@bar.com"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_resume_submission(self):
        """
        Test that resuming a form that has been deactivated is not possible.

        It's possible a submission is suspended while the form is still active,
        but time passes and by the time the submission is resumed, the form has been
        deactivated.

        The resume page should then display an error instead of redirecting to the
        UI/frontend.
        """
        self.client.force_login(user=self.user)
        submission = SubmissionFactory.create(form=self.form)
        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
