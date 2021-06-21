"""
Test comleting a submitted form.

Completion of the form is an explicit action (api-wise), by making a POST call on a
sub-resource.

The backend should perform total-form validation as part of this action.
"""
from unittest.mock import patch

from django.core import mail
from django.test import override_settings
from django.utils import timezone
from django.utils.translation import gettext as _

from django_capture_on_commit_callbacks import capture_on_commit_callbacks
from freezegun import freeze_time
from privates.test import temp_private_root
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
from ..models import SubmissionReport, SubmissionStep
from .factories import SubmissionFactory, SubmissionStepFactory
from .mixins import SubmissionsMixin


@temp_private_root()
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
            kwargs={"form_uuid_or_slug": step.form.uuid, "uuid": step.uuid},
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("download_url", response.data)

        report_response = self.client.get(response.data["download_url"])

        self.assertEqual(status.HTTP_200_OK, report_response.status_code)

        submission.refresh_from_db()
        self.assertEqual(submission.completed_on, timezone.now())

        # test that submission ID removed from session
        submissions_in_session = response.wsgi_request.session[SUBMISSIONS_SESSION_KEY]
        self.assertNotIn(str(submission.uuid), submissions_in_session)
        self.assertEqual(submissions_in_session, [])

    @patch("openforms.registrations.tasks.register_submission.delay")
    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_complete_submission_send_confirmation_email(self, delay_mock):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )
        def1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "email",
                        "type": "email",
                        "label": "Email",
                        "confirmationRecipient": True,
                    },
                ],
            }
        )
        step1 = FormStepFactory.create(form=form, form_definition=def1, optional=True)
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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

        delay_mock.assert_called_once_with(submission.id)

    @patch("openforms.registrations.tasks.register_submission.delay")
    def test_complete_submission_without_email_recipient(self, delay_mock):
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert that no e-mail was sent
        self.assertEqual(len(mail.outbox), 0)

        delay_mock.assert_called_once_with(submission.id)

    @patch("openforms.registrations.tasks.register_submission.delay")
    def test_complete_submission_send_confirmation_email_with_summary(self, delay_mock):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}, {{ bar }} and {{ hello }}. Submission summary: {% summary %}",
        )
        definition1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "email", "confirmationRecipient": True, "label": "Email"},
                    {"key": "foo", "showInEmail": True, "label": "Foo"},
                ],
            }
        )
        step1 = FormStepFactory.create(
            form=form, optional=True, form_definition=definition1
        )
        definition2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {"key": "bar", "label": "Bar", "showInEmail": True},
                    {"key": "hello", "label": "Hello", "showInEmail": False},
                ],
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
            self.client.post(endpoint)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertIn(
            "Information filled in: foovalue, barvalue and hellovalue.", message.body
        )
        self.assertIn("<th>Bar</th>", message.body)
        self.assertIn("<th>barvalue</th>", message.body)
        self.assertIn("<th>Foo</th>", message.body)
        self.assertIn("<th>foovalue</th>", message.body)
        self.assertNotIn("<th>Hello</th>", message.body)
        self.assertNotIn("<th>hellovalue</th>", message.body)

        delay_mock.assert_called_once_with(submission.id)

    @patch("openforms.registrations.tasks.register_submission.delay")
    def test_complete_submission_send_confirmation_email_to_many_recipients(
        self, delay_mock
    ):
        form = FormFactory.create()
        ConfirmationEmailTemplateFactory.create(
            form=form,
            subject="Confirmation mail",
            content="Information filled in: {{foo}}",
        )
        def1 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "single1",
                        "type": "email",
                        "label": "One",
                        "confirmationRecipient": True,
                    },
                    {
                        "key": "single2",
                        "type": "email",
                        "label": "Two",
                        "confirmationRecipient": True,
                    },
                ],
            }
        )
        def2 = FormDefinitionFactory.create(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "many",
                        "type": "email",
                        "label": "Many",
                        "multiple": True,
                        "confirmationRecipient": True,
                    },
                ],
            }
        )
        step1 = FormStepFactory.create(form=form, form_definition=def1, optional=True)
        step2 = FormStepFactory.create(
            form=form, form_definition=def2, optional=True
        )  # noqa
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"single1": "single1@test.nl", "single2": "single2@test.nl"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"many": ["many1@test.nl", "many2@test.nl"]},
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        with capture_on_commit_callbacks(execute=True):
            self.client.post(endpoint)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(
            set(message.to),
            {"single1@test.nl", "single2@test.nl", "many1@test.nl", "many2@test.nl"},
        )

        delay_mock.assert_called_once_with(submission.id)

    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_complete_submission_in_maintenance_mode(self):
        form = FormFactory.create(maintenance_mode=True)
        step1 = FormStepFactory.create(form=form, optional=False)
        step2 = FormStepFactory.create(form=form, optional=False)
        submission = SubmissionFactory.create(form=form)
        SubmissionStepFactory.create(
            submission=submission, form_step=step1, data={"foo": "bar"}
        )
        SubmissionStepFactory.create(
            submission=submission, form_step=step2, data={"foo": "bar"}
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertEqual(submission.completed_on, timezone.now())

    @patch("openforms.registrations.tasks.register_submission.delay")
    @patch("openforms.submissions.api.viewsets.send_confirmation_email")
    def test_complete_submission_creates_submission_report(
        self, m_confirmation_email, m_delay
    ):
        form = FormFactory.create(name="Test Form")
        submission = SubmissionFactory.create(form=form)
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-complete", kwargs={"uuid": submission.uuid})

        self.client.post(endpoint)

        report = SubmissionReport.objects.get()

        self.assertEqual(
            _("%(title)s: Submission report") % {"title": "Test Form"}, report.title
        )
        self.assertEqual(submission, report.submission)
        self.assertEqual(
            "Test_Form.pdf", report.content.name.split("/")[-1]
        )  # report.content.name contains the path too
