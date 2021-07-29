"""
Test suspending a form.

Suspension of the form is an explicit action (api-wise), by making a POST call on a
sub-resource.

The backend collects information to send an e-mail to the user for resuming, for
example.
"""
from unittest.mock import patch

from django.core import mail
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_capture_on_commit_callbacks import capture_on_commit_callbacks
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ..constants import SUBMISSIONS_SESSION_KEY
from .factories import SubmissionFactory, SubmissionStepFactory
from .mixins import SubmissionsMixin


class SubmissionSuspensionTests(SubmissionsMixin, APITestCase):
    def test_invalid_submission_id(self):
        submission = SubmissionFactory.create()
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_suspended_submission(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form, optional=False)
        step2 = FormStepFactory.create(form=form, optional=True)  # noqa
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission.refresh_from_db()
        self.assertEqual(submission.suspended_on, timezone.now())

        # test that submission ID is not removed from session
        submissions_in_session = response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]
        self.assertIn(str(submission.uuid), submissions_in_session)

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_missing_email(self, _mock):
        form = FormFactory.create()
        FormStepFactory.create(form=form, optional=False)
        step2 = FormStepFactory.create(form=form, optional=True)  # noqa
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "email",
                        "code": "required",
                        "reason": _("This field is required."),
                    }
                ],
            },
        )
        submission.refresh_from_db()
        self.assertIsNone(submission.suspended_on)

    def test_email_sent(self):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        with capture_on_commit_callbacks(execute=True) as callbacks:
            response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ["hello@open-forms.nl"])
        self.assertEqual(email.subject, _("Your form submission"))
