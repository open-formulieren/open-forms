"""
Test suspending a form.

Suspension of the form is an explicit action (api-wise), by making a POST call on a
sub-resource.

The backend collects information to send an e-mail to the user for resuming, for
example.
"""
from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import urljoin

from django.core import mail
from django.template import defaulttags
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_capture_on_commit_callbacks import capture_on_commit_callbacks
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory
from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory, FormStepFactory

from ..constants import SUBMISSIONS_SESSION_KEY
from ..tokens import submission_resume_token_generator
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

    @freeze_time("2021-11-15")
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
        self.assertEqual(
            email.subject,
            _("Saved form %(form_name)s") % {"form_name": submission.form.name},
        )

        self.assertIn(submission.form.name, email.body)
        self.assertIn(defaulttags.date(timezone.now()), email.body)

        submission.refresh_from_db()
        token = submission_resume_token_generator.make_token(submission)
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": token,
                "submission_uuid": submission.uuid,
            },
        )
        expected_resume_url = urljoin("http://testserver", resume_path)

        self.assertIn(expected_resume_url, email.body)

        datetime_removed = datetime(2021, 11, 22, 12, 00, 00, tzinfo=timezone.utc)

        self.assertIn(defaulttags.date(datetime_removed), email.body)

    @freeze_time("2020-11-15T12:00:00+01:00")
    def test_resume_url_does_not_work_after_submission_has_been_completed(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form, optional=False)
        step2 = FormStepFactory.create(form=form, optional=True)  # noqa
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)

        # Suspend the submission
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})
        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission.refresh_from_db()
        self.assertEqual(submission.suspended_on, timezone.now())

        # Get suspended link and resume submission
        submission.refresh_from_db()
        token = submission_resume_token_generator.make_token(submission)
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": token,
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(resume_path)
        self.assertEqual(response.status_code, 302)

        # Complete the submission
        submission.completed_on = timezone.now()
        submission.save(update_fields=["completed_on"])

        # Validate the link no longer works
        response = self.client.get(resume_path)
        self.assertEqual(response.status_code, 403)


class CSRFSubmissionSuspensionTests(SubmissionsMixin, APITestCase):
    def setUp(self):
        # install a different client class with enforced CSRF checks
        self.client = self.client_class(enforce_csrf_checks=True)
        super().setUp()

    def test_can_suspend_without_csrf_token_while_logged_in(self):
        """
        Assert that a CSRF token is not required if the user is authenticated.

        Regression test for #1627, where POST calls were blocked because of a missing
        CSRF token if the form was started BEFORE the user logged in to the admin
        area and the user logged in BEFORE copmleting/suspending the form (in another
        tab, for example).
        """
        user = UserFactory.create()
        self.client.force_login(
            user=user, backend="openforms.accounts.backends.UserModelEmailBackend"
        )
        submission = SubmissionFactory.from_data({"foo": "bar"})
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
