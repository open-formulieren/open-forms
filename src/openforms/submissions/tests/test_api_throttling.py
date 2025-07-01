import datetime

from django.conf import settings
from django.test import override_settings

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from .factories import SubmissionFactory
from .mixins import SubmissionsMixin

REST_FRAMEWORK_MODIFIED = settings.REST_FRAMEWORK.copy()
REST_FRAMEWORK_MODIFIED["DEFAULT_THROTTLE_RATES"]["pause"] = "3/minute"
REST_FRAMEWORK_MODIFIED["DEFAULT_THROTTLE_RATES"]["submit"] = "10/minute"


@override_settings(REST_FRAMEWORK=REST_FRAMEWORK_MODIFIED)
class APIThrottlingTest(SubmissionsMixin, APITestCase):
    def test_throttling_submit(self):
        """Assert that the API endpoint for completing submissions is throttled"""

        initial_datetime = datetime.datetime(
            year=2023, month=1, day=21, hour=11, minute=30, second=0
        )

        with freeze_time(initial_datetime) as frozen_datetime:
            # 10 requests per minute allowed
            for _ in range(10):
                submission = SubmissionFactory.create()
                self._add_submission_to_session(submission)
                endpoint = reverse(
                    "api:submission-complete", kwargs={"uuid": submission.uuid}
                )
                response = self.client.post(endpoint, {"privacy_policy_accepted": True})

                assert response.status_code == status.HTTP_200_OK, (
                    f"Expected: HTTP 200 (OK); Actual: HTTP {response.status_code}"
                )

            # Request #11 should fail with HTTP 429
            submission = SubmissionFactory.create()
            self._add_submission_to_session(submission)
            endpoint = reverse(
                "api:submission-complete", kwargs={"uuid": submission.uuid}
            )
            response = self.client.post(endpoint, {"privacy_policy_accepted": True})

            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS, (
                f"Expected: HTTP 429 (too many requests); Actual: HTTP {response.status_code}"
            )

            # Wait 1 minute for the next request
            frozen_datetime.tick(delta=datetime.timedelta(minutes=1))

            response = self.client.post(endpoint, {"privacy_policy_accepted": True})

            assert response.status_code == status.HTTP_200_OK, (
                f"Expected: HTTP 200 (OK); Actual: HTTP {response.status_code}"
            )

    def test_throttling_pause(self):
        """Assert that the API endpoint for suspending submissions is throttled"""

        initial_datetime = datetime.datetime(
            year=2023, month=1, day=21, hour=11, minute=30, second=0
        )

        with freeze_time(initial_datetime) as frozen_datetime:
            # 3 requests per minute allowed
            for _ in range(3):
                submission = SubmissionFactory.create()
                self._add_submission_to_session(submission)
                endpoint = reverse(
                    "api:submission-suspend", kwargs={"uuid": submission.uuid}
                )
                response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

                assert response.status_code == status.HTTP_201_CREATED, (
                    f"Expected: HTTP 201 (created); Actual: HTTP {response.status_code}"
                )

            # Request #4 should fail with HTTP 429
            submission = SubmissionFactory.create()
            self._add_submission_to_session(submission)
            endpoint = reverse(
                "api:submission-suspend", kwargs={"uuid": submission.uuid}
            )
            response = self.client.post(endpoint)

            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS, (
                f"Expected: HTTP 429 (too many requests); Actual: HTTP {response.status_code}"
            )

            # Wait 1 minute for the next request
            frozen_datetime.tick(delta=datetime.timedelta(minutes=1))

            response = self.client.post(endpoint, {"email": "hello@open-forms.nl"})

            assert response.status_code == status.HTTP_201_CREATED, (
                f"Expected: HTTP 201 (created); Actual: HTTP {response.status_code}"
            )
