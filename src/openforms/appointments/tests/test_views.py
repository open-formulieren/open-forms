import uuid
from datetime import UTC, datetime

from django.test import TestCase
from django.urls import reverse

from freezegun import freeze_time
from furl import furl

from openforms.authentication.contrib.digid.constants import DIGID_DEFAULT_LOA
from openforms.authentication.service import FORM_AUTH_SESSION_KEY, AuthAttribute
from openforms.frontend.tests import FrontendRedirectMixin
from openforms.submissions.constants import SUBMISSIONS_SESSION_KEY
from openforms.submissions.tests.factories import SubmissionFactory

from ..tokens import submission_appointment_token_generator
from .factories import AppointmentInfoFactory


@freeze_time("2021-07-15T21:15:00Z")
class VerifyCancelAppointmentLinkViewTests(FrontendRedirectMixin, TestCase):
    def test_good_token_and_submission_redirect_and_add_submission_to_session(self):
        submission = SubmissionFactory.create(
            completed=True, form_url="http://maykinmedia.nl/myform"
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=UTC),
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

        self.assertRedirectsToFrontend(
            response,
            frontend_base_url="http://maykinmedia.nl/myform",
            action="afspraak-annuleren",
            action_params={
                "time": "2021-07-21T12:00:00+00:00",
                "submission_uuid": str(submission.uuid),
            },
            fetch_redirect_response=False,
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
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=UTC),
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
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=UTC),
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
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=UTC),
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
            auth_info__plugin="digid",
            completed=True,
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=UTC),
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
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_url="http://testserver/myform/",
            completed=True,
            auth_info__value="123456782",
            auth_info__plugin="digid",
        )
        start_time = datetime(2021, 7, 21, 12, 00, 00, tzinfo=UTC)
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

        # Add form_auth to session, as the authentication plugin would do it
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": AuthAttribute.bsn,
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertRedirectsToFrontend(
            response,
            frontend_base_url=submission.form_url,
            action="afspraak-annuleren",
            action_params={
                "time": start_time.isoformat(),
                "submission_uuid": str(submission.uuid),
            },
            fetch_redirect_response=False,
        )

        self.assertIn(SUBMISSIONS_SESSION_KEY, self.client.session)
        self.assertIn(
            str(submission.uuid), self.client.session[SUBMISSIONS_SESSION_KEY]
        )

    def test_invalid_auth_plugin_raises_exception(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_info__plugin="wrong-plugin",
            form_url="http://testserver/myform/",
            completed=True,
            auth_info__value="123456782",
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=UTC),
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
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_invalid_auth_attribute_raises_exception(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            form_url="http://testserver/myform/",
            completed=True,
            auth_info__plugin="digid",
            auth_info__value="123456782",
            auth_info__attribute=AuthAttribute.kvk,
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=UTC),
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
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)

    def test_invalid_auth_value_raises_exception(self):
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__formstep__form_definition__login_required=True,
            auth_info__plugin="digid",
            form_url="http://testserver/myform/",
            completed=True,
            auth_info__value="wrong-bsn",
        )
        AppointmentInfoFactory.create(
            submission=submission,
            registration_ok=True,
            start_time=datetime(2021, 7, 21, 12, 00, 00, tzinfo=UTC),
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
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.client.get(endpoint)

        self.assertEqual(403, response.status_code)
        self.assertNotIn(SUBMISSIONS_SESSION_KEY, self.client.session)
