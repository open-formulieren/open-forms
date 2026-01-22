"""
Test suspending a form.

Suspension of the form is an explicit action (api-wise), by making a POST call on a
sub-resource.

The backend collects information to send an e-mail to the user for resuming, for
example.
"""

from datetime import datetime
from unittest.mock import patch
from urllib.parse import urljoin

from django.core import mail
from django.template import defaulttags
from django.test import override_settings, tag
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.config.models import GlobalConfiguration
from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormRegistrationBackendFactory,
    FormStepFactory,
)
from openforms.utils.tests.cache import clear_caches

from ..constants import SUBMISSIONS_SESSION_KEY
from ..tokens import submission_resume_token_generator
from .factories import SubmissionFactory, SubmissionStepFactory
from .mixins import SubmissionsMixin


class SubmissionSuspensionTests(SubmissionsMixin, APITestCase):
    def setUp(self):
        # clear caches to avoid problems with throttling; @override_settings not working
        # see https://github.com/encode/django-rest-framework/issues/6030
        self.addCleanup(clear_caches)
        super().setUp()

    def test_invalid_submission_id(self):
        submission = SubmissionFactory.create()
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_suspended_submission(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        step2 = FormStepFactory.create(form=form)
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

    @freeze_time("2020-12-11T10:53:19+01:00")
    @override_settings(LANGUAGE_CODE="en")
    def test_suspended_submission_not_allowed(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__suspension_allowed=False,
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "permission_denied")

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_missing_email(self, _mock):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        step2 = FormStepFactory.create(form=form)
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
    @patch(
        "openforms.submissions.api.serializers.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(
            save_form_email_subject="Saved form {{ form_name }}"
        ),
    )
    def test_email_sent(self, *mocks):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ["hello@open-forms.nl"])
        self.assertEqual(email.subject, f"Saved form {submission.form.name}")

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

    @freeze_time("2021-11-15")
    @patch("openforms.submissions.api.serializers.GlobalConfiguration.get_solo")
    @override_settings(LANGUAGE_CODE="nl")
    def test_email_sent_with_custom_configuration(self, m_solo):
        m_solo.return_value = GlobalConfiguration(
            save_form_email_subject="The Subject: {{ form_name }}",
            save_form_email_content="The Content: {{ form_name }} ({{ save_date }})",
        )

        submission = SubmissionFactory.create(form__name="Form 000")
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ["hello@open-forms.nl"])
        self.assertEqual(email.subject, "The Subject: Form 000")
        self.assertEqual(
            email.body.strip(), "The Content: Form 000 (15 november 2021 01:00)"
        )

    @freeze_time("2020-11-15T12:00:00+01:00")
    def test_resume_url_does_not_work_after_submission_has_been_completed(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        step2 = FormStepFactory.create(form=form)
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

    @tag("gh-2785")
    def test_identifying_attributes_hashed_on_suspend(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form_url="http://tests/myform/",
            auth_info__plugin="digid",
            auth_info__value="123456789",
        )
        form_step = submission.form.formstep_set.first()
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"foo": "bar"},
        )
        self._add_submission_to_session(submission)

        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})
        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        submission.refresh_from_db()

        # Assert that submission is suspended
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(submission.suspended_on)

        # Assert that identifying attribute is hashed
        self.assertNotEqual(submission.auth_info.value, "123456789")
        self.assertTrue(submission.auth_info.attribute_hashed)

    @tag("gh-4502")
    def test_registration_backend_logic_not_persisted_on_suspend(self):
        submission = SubmissionFactory.create(form__generate_minimal_setup=True)
        FormRegistrationBackendFactory.create(
            key="my-registration",
            backend="demo",
            form=submission.form,
        )
        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.set_registration_backend,
                        "value": "my-registration",
                    },
                }
            ],
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission.refresh_from_db()
        self.assertEqual(submission.finalised_registration_backend_key, "")

    def test_submission_cannot_be_suspended_when_already_completed(self):
        form = FormFactory.create()
        step = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form, completed=True)
        SubmissionStepFactory.create(
            submission=submission, form_step=step, data={"foo": "bar"}
        )

        self._add_submission_to_session(submission)

        # Suspend the submission
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})
        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_resuming_submission_and_completed_steps(self):
        form = FormFactory.create()

        step1 = FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step1, data={"test1": "bar"}
        )

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-suspend", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission.refresh_from_db()
        self.assertEqual(submission.suspended_on, timezone.now())
        self.assertFalse(submission.steps[0].completed)
