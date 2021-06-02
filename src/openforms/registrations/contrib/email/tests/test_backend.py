from datetime import datetime

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

import requests_mock

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.registrations.contrib.email.plugin import email_submission
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)


@requests_mock.Mocker()
class EmailBackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.form = FormFactory.create()
        cls.fd = FormDefinitionFactory.create()
        cls.fs = FormStepFactory.create(form=cls.form, form_definition=cls.fd)

    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    def test_submission_with_email_backend(self, m):
        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
        )

        data = {"foo": "bar", "some_list": ["value1", "value2"]}

        submission = SubmissionFactory.create(form=self.form)
        SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data=data
        )
        submission.completed_on = timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0))
        submission.save()

        email_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(
            message.subject,
            f"[Open Forms] {submission.form.name} - submission {submission.uuid}",
        )
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["foo@bar.nl", "bar@foo.nl"])

        # Check that the template is used
        self.assertIn('<table border="0">', message.body)
        self.assertIn(
            f"Submission details for {self.form.name} (submitted on 12:00:00 01-01-2021)",
            message.body,
        )
        self.assertIn("foo: bar", message.body)
        self.assertIn("some_list: value1, value2", message.body)

    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    def test_submission_with_email_backend_strip_out_urls(self, m):
        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
        )

        data = {
            "foo": "https://someurl.com",
        }

        submission = SubmissionFactory.create(form=self.form)
        SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data=data
        )
        submission.completed_on = timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0))
        submission.save()

        email_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(
            message.subject,
            f"[Open Forms] {submission.form.name} - submission {submission.uuid}",
        )
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["foo@bar.nl", "bar@foo.nl"])

        # Check that the template is used
        self.assertIn('<table border="0">', message.body)
        self.assertIn(
            f"Submission details for {self.form.name} (submitted on 12:00:00 01-01-2021)",
            message.body,
        )
        self.assertNotIn("https://someurl.com", message.body)

    @override_settings(DEFAULT_FROM_EMAIL="info@open-forms.nl")
    def test_submission_with_email_backend_keep_allowed_urls(self, m):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["https://allowed.com"]

        email_form_options = dict(
            to_emails=["foo@bar.nl", "bar@foo.nl"],
        )

        data = {
            "foo": "https://allowed.com",
        }

        submission = SubmissionFactory.create(form=self.form)
        SubmissionStepFactory.create(
            submission=submission, form_step=self.fs, data=data
        )
        submission.completed_on = timezone.make_aware(datetime(2021, 1, 1, 12, 0, 0))
        submission.save()

        email_submission(submission, email_form_options)

        # Verify that email was sent
        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertEqual(
            message.subject,
            f"[Open Forms] {submission.form.name} - submission {submission.uuid}",
        )
        self.assertEqual(message.from_email, "info@open-forms.nl")
        self.assertEqual(message.to, ["foo@bar.nl", "bar@foo.nl"])

        # Check that the template is used
        self.assertIn('<table border="0">', message.body)
        self.assertIn(
            f"Submission details for {self.form.name} (submitted on 12:00:00 01-01-2021)",
            message.body,
        )
        self.assertNotIn("https://allowed.com", message.body)
