import uuid
from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from freezegun import freeze_time
from furl import furl

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.constants import SUBMISSIONS_SESSION_KEY
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ..tokens import submission_appointment_token_generator
from .factories import AppointmentInfoFactory


@freeze_time("2021-07-15T21:15:00Z")
class VerifyCancelAppointmentLinkViewTests(TestCase):
    def test_good_token_and_submission_redirect_and_add_submission_to_session(self):
        submission = SubmissionFactory.create(
            completed=True, form_url="http://maykinmedia.nl/myform"
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # one day after token generation
        with freeze_time("2021-07-16T21:15:00Z"):
            response = self.client.get(endpoint)

        expected_redirect_url = (
            furl("http://maykinmedia.nl/myform/afspraak-annuleren")
            .add(
                {
                    "time": "2021-07-21T12:00:00+00:00",
                    "submission_uuid": str(submission.uuid),
                }
            )
            .url
        )
        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )
        # Assert submission is stored in session
        self.assertIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

    def test_403_response_with_unfound_submission(self):
        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "irrelevant",
                "submission_uuid": uuid.uuid4(),
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_403_response_with_bad_token(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": "bad",
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_invalid_after_appointment_time(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with freeze_time("2021-07-22T12:00:00Z"):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_valid_on_same_day_appointment(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with freeze_time("2021-07-21T11:59:59Z"):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 302)

    def test_redirects_to_auth_if_form_requires_login(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_plugin="digid",
            completed=True,
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
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
            completed=True,
            bsn="123456782",
        )
        start_time = datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=start_time,
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )
        expected_redirect_url = furl(submission.form_url)
        expected_redirect_url /= "afspraak-annuleren"
        expected_redirect_url.add(
            {
                "time": start_time.isoformat(),
                "submission_uuid": str(submission.uuid),
            }
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
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
            completed=True,
            bsn="123456782",
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
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
            completed=True,
            kvk="123456782",
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
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
            completed=True,
            bsn="wrong-bsn",
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)


@freeze_time("2021-07-15T21:15:00Z")
class VerifyChangeAppointmentLinkViewTests(TestCase):
    def test_good_token_and_submission_redirect_and_add_submission_to_session(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "product",
                    "appointments": {"showProducts": True},
                    "label": "Product",
                },
                {
                    "key": "time",
                    "appointments": {"showTimes": True},
                    "label": "Time",
                },
            ],
            submitted_data={
                "product": {"identifier": "79", "name": "Paspoort"},
                "time": "2021-08-25T17:00:00",
            },
            form_url="http://maykinmedia.nl/myform/",
        )
        form_definition = submission.form.formstep_set.get().form_definition
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-change-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # one day after token generation
        with freeze_time("2021-07-16T21:15:00Z"):
            response = self.client.get(endpoint)

        new_submission = Submission.objects.exclude(id=submission.id).get()
        expected_redirect_url = (
            f"http://maykinmedia.nl/myform/stap/{form_definition.slug}"
            f"?submission_uuid={new_submission.uuid}"
        )

        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )
        # Assert new submission was created
        self.assertEqual(Submission.objects.count(), 2)
        # Assert old submission not stored in session
        self.assertNotIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )
        # Assert new  submission is stored in session
        self.assertIn(
            str(new_submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

    def test_403_response_with_unfound_submission(self):
        endpoint = reverse(
            "appointments:appointments-verify-change-appointment-link",
            kwargs={
                "token": "irrelevant",
                "submission_uuid": uuid.uuid4(),
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_403_response_with_bad_token(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-change-appointment-link",
            kwargs={
                "token": "bad",
                "submission_uuid": submission.uuid,
            },
        )

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_invalid_after_appointment_time(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-change-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with freeze_time("2021-07-22T12:00:00Z"):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 403)

    def test_token_valid_on_same_day_appointment(self):
        submission = SubmissionFactory.from_components(
            completed=True,
            components_list=[
                {
                    "key": "product",
                    "appointments": {"showProducts": True},
                    "label": "Product",
                },
                {
                    "key": "time",
                    "appointments": {"showTimes": True},
                    "label": "Time",
                },
            ],
            submitted_data={
                "product": {"identifier": "79", "name": "Paspoort"},
                "time": "2021-08-25T17:00:00",
            },
            form_url="http://maykinmedia.nl/myform/",
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-change-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with freeze_time("2021-07-21T11:59:59Z"):
            response = self.client.get(endpoint)

        self.assertEqual(response.status_code, 302)

    def test_redirect_to_first_step_when_appointment_form_definition_can_not_be_found(
        self,
    ):
        form = FormFactory.create()
        submission = SubmissionFactory.create(
            form=form, completed=True, form_url="http://maykinmedia.nl/myform/"
        )
        SubmissionStepFactory.create(
            form_step__form=form,
            form_step__form_definition__slug="step-1",
            form_step__form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "name",
                        "label": "Name",
                    },
                ],
            },
            submission=submission,
            data={
                "Name": "Maykin",
            },
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step__form=form,
            form_step__form_definition__slug="step-2",
            form_step__form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "appointments": {"showProducts": False},
                        "label": "Product",
                    },
                    {
                        "key": "time",
                        "appointments": {"showTimes": False},
                        "label": "Time",
                    },
                ],
            },
            data={
                "product": {"identifier": "79", "name": "Paspoort"},
                "time": "2021-08-25T17:00:00",
            },
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=timezone.utc),
        )

        endpoint = reverse(
            "appointments:appointments-verify-change-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        # one day after token generation
        with freeze_time("2021-07-16T21:15:00Z"):
            response = self.client.get(endpoint)

        new_submission = Submission.objects.exclude(id=submission.id).get()
        expected_redirect_url = f"http://maykinmedia.nl/myform/stap/step-1?submission_uuid={new_submission.uuid}"
        self.assertRedirects(
            response, expected_redirect_url, fetch_redirect_response=False
        )
