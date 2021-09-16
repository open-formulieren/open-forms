from django.test import override_settings
from django.urls import reverse

import requests_mock
from rest_framework import status
from rest_framework.test import APITestCase

from ...tests.factories import SubmissionFactory
from ...tests.mixins import SubmissionsMixin


@requests_mock.Mocker()
@override_settings(RECAPTCHA_PROJECT_ID="test-project-id", RECAPTCHA_API_KEY="test-key")
class CaptchaViewTest(SubmissionsMixin, APITestCase):
    def test_requires_active_submission(self, m):
        response = self.client.post(reverse("api:submissions:captcha-assessment"))

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_generate_human_assessment(self, m):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        # Mock the call to the Google API that makes the token assessment
        m.post(
            "https://recaptchaenterprise.googleapis.com/v1beta1/projects/test-project-id/assessments?key=test-key",
            json={
                "name": "projects/000000000000/assessments/1111111111111111",
                "event": {
                    "token": "thisIsAFakeToken",
                    "siteKey": "test-key",
                    "userAgent": "",
                    "userIpAddress": "",
                    "expectedAction": "formSubmission",
                },
                "score": 0.9,
                "tokenProperties": {
                    "valid": True,
                    "invalidReason": "INVALID_REASON_UNSPECIFIED",
                    "hostname": "localhost",
                    "action": "formSubmission",
                    "createTime": "2021-09-16T14:59:09.866Z",
                },
                "reasons": [],
            },
        )

        response = self.client.post(
            reverse("api:submissions:captcha-assessment"),
            data={"token": "thisIsAFakeToken", "action": "formSubmission"},
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.json()["allowSubmission"])

    def test_generate_bot_assessment(self, m):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        # Mock the call to the Google API that makes the token assessment
        m.post(
            "https://recaptchaenterprise.googleapis.com/v1beta1/projects/test-project-id/assessments?key=test-key",
            json={
                "name": "projects/000000000000/assessments/1111111111111111",
                "event": {
                    "token": "thisIsAFakeToken",
                    "siteKey": "test-key",
                    "userAgent": "",
                    "userIpAddress": "",
                    "expectedAction": "formSubmission",
                },
                "score": 0.4,
                "tokenProperties": {
                    "valid": True,
                    "invalidReason": "INVALID_REASON_UNSPECIFIED",
                    "hostname": "localhost",
                    "action": "formSubmission",
                    "createTime": "2021-09-16T14:59:09.866Z",
                },
                "reasons": [],
            },
        )

        response = self.client.post(
            reverse("api:submissions:captcha-assessment"),
            data={"token": "thisIsAFakeToken", "action": "formSubmission"},
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertFalse(response.json()["allowSubmission"])

    def test_invalid_token(self, m):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        # Mock the call to the Google API that makes the token assessment
        m.post(
            "https://recaptchaenterprise.googleapis.com/v1beta1/projects/test-project-id/assessments?key=test-key",
            json={
                "name": "projects/844488852392/assessments/fb332488a8000000",
                "event": {
                    "token": "thisIsAFakeToken",
                    "siteKey": "test-key",
                    "userAgent": "",
                    "userIpAddress": "",
                    "expectedAction": "formSubmission",
                },
                "score": 0,
                "tokenProperties": {
                    "valid": False,
                    "invalidReason": "MALFORMED",
                    "hostname": "",
                    "action": "",
                },
                "reasons": [],
            },
        )

        response = self.client.post(
            reverse("api:submissions:captcha-assessment"),
            data={"token": "thisIsAFakeToken", "action": "formSubmission"},
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_wrong_user_action(self, m):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        # Mock the call to the Google API that makes the token assessment
        m.post(
            "https://recaptchaenterprise.googleapis.com/v1beta1/projects/test-project-id/assessments?key=test-key",
            json={
                "name": "projects/000000000000/assessments/1111111111111111",
                "event": {
                    "token": "thisIsAFakeToken",
                    "siteKey": "test-key",
                    "userAgent": "",
                    "userIpAddress": "",
                    "expectedAction": "formSubmission",
                },
                "score": 0.9,
                "tokenProperties": {
                    "valid": True,
                    "invalidReason": "INVALID_REASON_UNSPECIFIED",
                    "hostname": "localhost",
                    "action": "wrongAction",
                    "createTime": "2021-09-16T14:59:09.866Z",
                },
                "reasons": [],
            },
        )

        response = self.client.post(
            reverse("api:submissions:captcha-assessment"),
            data={"token": "thisIsAFakeToken", "action": "formSubmission"},
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
