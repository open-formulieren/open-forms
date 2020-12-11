"""
Test comleting a submitted form.

Completion of the form is an explicit action (api-wise), by making a POST call on a
sub-resource.

The backend should perform total-form validation as part of this action.
"""
from django.utils import timezone

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.core.tests.factories import FormFactory, FormStepFactory

from ..constants import SUBMISSIONS_SESSION_KEY
from ..models import SubmissionStep
from .factories import SubmissionFactory, SubmissionStepFactory
from .mixins import SubmissionsMixin


class SubmissionCompletionTests(SubmissionsMixin, APITestCase):
    def test_invalid_submission_id(self):
        submission = SubmissionFactory.create()
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_all_required_steps_validated(self):
        step = FormStepFactory.create(optional=False)
        submission = SubmissionFactory.create(form=step.form)
        self._add_submission_to_session(submission)
        form_step_url = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid": step.form.uuid, "uuid": step.uuid},
        )
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})
        assert not SubmissionStep.objects.filter(
            submission=submission, form_step=step
        ).exists()

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.json()
        self.assertEqual(len(errors["incompleteSteps"]), 1)
        self.assertEqual(
            errors["incompleteSteps"],
            [{"formStep": f"http://testserver{form_step_url}"}],
        )

    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_complete_submission(self):
        form = FormFactory.create()
        step1 = FormStepFactory.create(form=form, optional=False)
        step2 = FormStepFactory.create(form=form, optional=True)  # noqa
        step3 = FormStepFactory.create(form=form, optional=False)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step1, data={"foo": "bar"}
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=step3, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        submission.refresh_from_db()
        self.assertEqual(submission.completed_on, timezone.now())

        # test that submission ID removed from session
        submissions_in_session = response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]
        self.assertNotIn(str(submission.uuid), submissions_in_session)
        self.assertEqual(submissions_in_session, [])
