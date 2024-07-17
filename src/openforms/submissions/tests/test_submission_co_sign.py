from unittest.mock import patch

from django.test import override_settings
from django.urls import resolve

from furl import furl
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY
from openforms.config.models import GlobalConfiguration

from ..constants import SUBMISSIONS_SESSION_KEY
from .factories import SubmissionFactory
from .mixins import SubmissionsMixin


class SubmissionCoSignStatusTests(SubmissionsMixin, APITestCase):
    def test_submission_id_not_in_session(self):
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": "digid",
                "identifier": "123456782",
                "representation": "B. My Tires",
                "fields": {
                    "first_name": "Bono",
                    "last_name": "My Tires",
                },
            }
        )
        endpoint = reverse("api:submission-co-sign", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_submission_co_sign_status(self):
        """
        Assert that the identifier is not present in the API response.
        """
        submission = SubmissionFactory.create(
            co_sign_data={
                "plugin": "digid",
                "identifier": "123456782",
                "representation": "B. My Tires",
                "fields": {
                    "first_name": "Bono",
                    "last_name": "My Tires",
                },
            }
        )
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-co-sign", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(
            response.json(),
            {
                "coSigned": True,
                "representation": "B. My Tires",
            },
        )

    def test_submission_co_sign_status_no_co_sign(self):
        submission = SubmissionFactory.create(co_sign_data={})
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-co-sign", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(
            response.json(),
            {
                "coSigned": False,
                "representation": "",
            },
        )


class SubmissionCosignEndpointTests(SubmissionsMixin, APITestCase):
    def test_submission_must_be_in_session(self):
        submission = SubmissionFactory.from_components(
            components_list=[{"type": "cosign", "key": "cosign"}],
            submitted_data={
                "cosign": "test@example.com",
            },
        )

        endpoint = reverse("api:submission-cosign", kwargs={"uuid": submission.uuid})
        response = self.client.post(endpoint)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_submission_must_be_completed(self):
        submission = SubmissionFactory.from_components(
            components_list=[{"type": "cosign", "key": "cosign"}],
            submitted_data={
                "cosign": "test@example.com",
            },
            completed=False,
        )

        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-cosign", kwargs={"uuid": submission.uuid})
        response = self.client.post(endpoint, data={"privacy_policy_accepted": True})

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_user_must_have_authenticated_with_allowed_plugin(self):
        submission = SubmissionFactory.from_components(
            form__authentication_backends=["eherkenning"],
            components_list=[{"type": "cosign", "key": "cosign"}],
            submitted_data={
                "cosign": "test@example.com",
            },
            completed=True,
        )

        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-cosign", kwargs={"uuid": submission.uuid})
        response = self.client.post(endpoint)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_cosign_happy_flow_calls_on_cosign_task(self):
        submission = SubmissionFactory.from_components(
            form__authentication_backends=["digid"],
            components_list=[
                {"type": "cosign", "key": "cosign", "authPlugin": "digid"}
            ],
            submitted_data={
                "cosign": "test@example.com",
            },
            registration_success=True,
        )

        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-cosign", kwargs={"uuid": submission.uuid})

        with patch(
            "openforms.forms.models.form.GlobalConfiguration.get_solo",
            return_value=GlobalConfiguration(
                ask_statement_of_truth=True, ask_privacy_consent=True
            ),
        ):
            response = self.client.post(
                endpoint,
                data={
                    "privacy_policy_accepted": True,
                    "statement_of_truth_accepted": True,
                },
            )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.json()

        self.assertIn("reportDownloadUrl", data)

        match = resolve(furl(data["reportDownloadUrl"]).path)

        self.assertEqual(match.view_name, "submissions:download-submission")

        submission.refresh_from_db()

        self.assertTrue(submission.cosign_complete)
        self.assertTrue(submission.cosign_privacy_policy_accepted)
        self.assertTrue(submission.cosign_statement_of_truth_accepted)

        session = self.client.session
        ids = session.get(SUBMISSIONS_SESSION_KEY, [])

        self.assertNotIn(submission.uuid, ids)

    @override_settings(LANGUAGE_CODE="en")
    def test_cosign_did_not_accept_privacy_policy(self):
        submission = SubmissionFactory.from_components(
            form__authentication_backends=["digid"],
            components_list=[{"type": "cosign", "key": "cosign"}],
            submitted_data={
                "cosign": "test@example.com",
            },
            completed=True,
        )

        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-cosign", kwargs={"uuid": submission.uuid})

        response = self.client.post(endpoint, data={"privacy_policy_accepted": False})

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        data = response.json()

        self.assertEqual(data["invalidParams"][0]["name"], "privacyPolicyAccepted")
        self.assertEqual(
            data["invalidParams"][0]["reason"],
            "You must accept the privacy policy.",
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_cosign_did_not_accept_truth_declaration(self):
        submission = SubmissionFactory.from_components(
            form__authentication_backends=["digid"],
            components_list=[{"type": "cosign", "key": "cosign"}],
            submitted_data={
                "cosign": "test@example.com",
            },
            completed=True,
        )

        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-cosign", kwargs={"uuid": submission.uuid})

        with self.subTest("Truth declaration not in body"):
            with patch(
                "openforms.forms.models.form.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(ask_statement_of_truth=True),
            ):
                response = self.client.post(
                    endpoint, data={"privacy_policy_accepted": True}
                )

            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

            data = response.json()

            self.assertEqual(
                data["invalidParams"][0]["name"], "statementOfTruthAccepted"
            )
            self.assertEqual(
                data["invalidParams"][0]["reason"],
                "You must declare the form to be filled out truthfully.",
            )

        with self.subTest("Truth declaration in body but false"):
            with patch(
                "openforms.forms.models.form.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(ask_statement_of_truth=True),
            ):
                response = self.client.post(
                    endpoint,
                    data={
                        "privacy_policy_accepted": True,
                        "statement_of_truth_accepted": False,
                    },
                )

            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

            data = response.json()

            self.assertEqual(
                data["invalidParams"][0]["name"], "statementOfTruthAccepted"
            )
            self.assertEqual(
                data["invalidParams"][0]["reason"],
                "You must declare the form to be filled out truthfully.",
            )
