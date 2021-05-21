"""
Test comleting a submitted form.

Completion of the form is an explicit action (api-wise), by making a POST call on a
sub-resource.

The backend should perform total-form validation as part of this action.
"""
from django.core import mail
from django.test import override_settings
from django.utils import timezone

from django_capture_on_commit_callbacks import capture_on_commit_callbacks
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.emails.tests.factories import ConfirmationEmailTemplateFactory
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

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

    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_complete_submission_send_confirmation_email(self):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )
        step1 = FormStepFactory.create(form=form, optional=True)
        step2 = FormStepFactory.create(form=form, optional=True)  # noqa
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step1, data={"email": "test@test.nl"}
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        with capture_on_commit_callbacks(execute=True):
            response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        submission.refresh_from_db()
        self.assertEqual(submission.completed_on, timezone.now())

        # test that submission ID removed from session
        submissions_in_session = response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]
        self.assertNotIn(str(submission.uuid), submissions_in_session)
        self.assertEqual(submissions_in_session, [])

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, "Confirmation mail")
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["test@test.nl"])

        # Check that the template is used
        self.assertIn('<table border="0">', message.body)
        self.assertIn("Information filled in: bar", message.body)

    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_complete_submission_send_confirmation_email_custom_property_name(self):
        form = FormFactory.create(email_property_name="custom_email")
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )
        step1 = FormStepFactory.create(form=form, optional=True)
        step2 = FormStepFactory.create(form=form, optional=True)  # noqa
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"custom_email": "test@test.nl"},
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        with capture_on_commit_callbacks(execute=True):
            response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        submission.refresh_from_db()
        self.assertEqual(submission.completed_on, timezone.now())

        # test that submission ID removed from session
        submissions_in_session = response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]
        self.assertNotIn(str(submission.uuid), submissions_in_session)
        self.assertEqual(submissions_in_session, [])

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(message.subject, "Confirmation mail")
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["test@test.nl"])

        # Check that the template is used
        self.assertIn('<table border="0">', message.body)
        self.assertIn("Information filled in: bar", message.body)

    def test_complete_submission_without_email_recipient(self):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )
        step1 = FormStepFactory.create(form=form, optional=True)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(submission=submission, form_step=step1, data={})
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        with capture_on_commit_callbacks(execute=True):
            response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # assert that no e-mail was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_complete_submission_send_confirmation_email_with_summary(self):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}, {{ bar }} and {{ hello }}. Submission summary: {% summary %}",
        )
        definition1 = FormDefinitionFactory.create(
            configuration={
                "index": 0,
                "configuration": {
                    "display": "form",
                    "components": [
                        {"key": "foo", "showInEmail": True},
                    ],
                },
            }
        )
        step1 = FormStepFactory.create(
            form=form, optional=True, form_definition=definition1
        )
        definition2 = FormDefinitionFactory.create(
            configuration={
                "index": 0,
                "configuration": {
                    "display": "form",
                    "components": [
                        {"key": "bar", "showInEmail": True},
                        {"key": "hello", "showInEmail": False},
                    ],
                },
            }
        )
        step2 = FormStepFactory.create(
            form=form, optional=True, form_definition=definition2
        )

        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"foo": "foovalue", "email": "test@test.nl"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"bar": "barvalue", "hello": "hellovalue"},
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        with capture_on_commit_callbacks(execute=True):
            response = self.client.post(endpoint)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertIn(
            "Information filled in: foovalue, barvalue and hellovalue.", message.body
        )
        self.assertIn("<th>bar</th>", message.body)
        self.assertIn("<th>barvalue</th>", message.body)
        self.assertIn("<th>foo</th>", message.body)
        self.assertIn("<th>foovalue</th>", message.body)
        self.assertNotIn("<th>hello</th>", message.body)
        self.assertNotIn("<th>hellovalue</th>", message.body)
