import uuid
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse

from freezegun import freeze_time
from furl import furl

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY
from openforms.config.models import GlobalConfiguration

from ..constants import SUBMISSIONS_SESSION_KEY
from ..tokens import submission_resume_token_generator
from .factories import SubmissionFactory, SubmissionStepFactory


class SubmissionResumeViewTests(TestCase):
    def test_good_token_and_submission_redirect_and_add_submission_to_session(self):
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
            form_url="http://maykinmedia.nl/myform",
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

        f = furl(submission.form_url)
        # furl adds paths with the /= operator
        f /= "stap"
        f /= submission.get_last_completed_step().form_step.form_definition.slug
        # Add the submission uuid to the query param
        f.add({"submission_uuid": submission.uuid})

        expected_redirect_url = f.url
        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )
        # Assert submission is stored in session
        self.assertIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

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

    def test_redirects_to_auth_if_form_requires_login(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_plugin="digid",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.first(),
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )
        expected_redirect_url = furl(
            f"http://testserver/auth/{submission.form.slug}/digid/start"
        )
        expected_redirect_url.args["next"] = f"http://testserver{endpoint}"

        response = self.client.get(endpoint)

        self.assertRedirects(
            response, expected_redirect_url.url, fetch_redirect_response=False
        )
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_after_successful_auth_redirects_to_form(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_plugin="digid",
            form_url="http://testserver/myform/",
            bsn="123456782",
        )
        form_step = submission.form.formstep_set.first()
        SubmissionStepFactory.create(
            submission=submission,
            form_step=form_step,
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )
        expected_redirect_url = furl(submission.form_url)
        expected_redirect_url /= "stap"
        expected_redirect_url /= form_step.form_definition.slug
        expected_redirect_url.args["submission_uuid"] = submission.uuid

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertRedirects(
            response, expected_redirect_url.url, fetch_redirect_response=False
        )
        self.assertIn(SUBMISSIONS_SESSION_KEY, self.client.session)
        self.assertIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

    def test_invalid_auth_plugin_raises_exception(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_plugin="wrong-plugin",
            form_url="http://testserver/myform/",
            bsn="123456782",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.first(),
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_invalid_auth_attribute_raises_exception(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_plugin="digid",
            form_url="http://testserver/myform/",
            kvk="123456782",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.first(),
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_invalid_auth_value_raises_exception(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_plugin="digid",
            form_url="http://testserver/myform/",
            bsn="wrong-bsn",
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.first(),
            data={"foo": "bar"},
        )

        endpoint = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)
