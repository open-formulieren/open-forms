import uuid
from datetime import timedelta
from urllib.parse import urljoin

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from freezegun import freeze_time

from openforms.config.models import GlobalConfiguration
from openforms.submissions.constants import SUBMISSIONS_SESSION_KEY
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ..tokens import submission_resume_token_generator


class SubmissionResumeViewTests(TestCase):
    def test_good_token_and_submission_redirect_and_add_submission_to_session(self):
        config = GlobalConfiguration.get_solo()
        config.sdk_url = "http://maykinmedia-sdk.nl/"
        config.save()

        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
        )
        # add a second step
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form=submission.form,
            form_step__optional=False,
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        expected_redirect_url = urljoin(
            config.sdk_url,
            "stap",
            submission.get_last_completed_step().form_step.form_definition.slug,
        )
        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )
        # Assert submission is stored in session
        self.assertIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

    def test_runtime_error_raised_when_no_sdk_url_is_specified(self):
        config = GlobalConfiguration.get_solo()
        config.sdk_url = ""
        config.save()

        submission = SubmissionFactory.create()

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with self.assertRaises(RuntimeError):
            self.client.get(endpoint)

    def test_403_response_with_unfound_submission(self):
        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": "irrelevant",
                "submission_uuid": uuid.uuid4(),
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_403_response_with_bad_token(self):
        submission = SubmissionFactory.create()

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": "bad",
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_invalid_after_submission_incomplete_invalid_time(self):
        config = GlobalConfiguration.get_solo()
        config.sdk_url = "http://maykinmedia-sdk.nl/"
        config.save()

        submission = SubmissionFactory.create()

        with freeze_time(
            submission.created_on
            - timedelta(
                days=(
                    submission_resume_token_generator.get_token_timeout_days(submission)
                    + 1
                )
            )
        ):
            token = submission_resume_token_generator.make_token(submission)

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": token,
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_valid_on_same_day(self):
        config = GlobalConfiguration.get_solo()
        config.sdk_url = "http://maykinmedia-sdk.nl/"
        config.save()

        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                    "confirmationRecipient": True,
                },
            ],
            submitted_data={"email": "test@test.nl"},
        )
        # add a second step
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form=submission.form,
            form_step__optional=False,
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 302)
