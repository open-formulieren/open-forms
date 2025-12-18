from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin


class PingViewTests(SubmissionsMixin, APITestCase):
    endpoint = reverse_lazy("api:ping")

    def test_not_authenticated(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_staff_user(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user(self):
        user = StaffUserFactory.create()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_anon_user_with_submission(self):
        submission = SubmissionFactory.create()
        self._add_submission_to_session(submission)

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class HealthCheckViewTests(APITestCase):
    endpoint = reverse_lazy("api:health")

    def test_health_check_returns_204(self):
        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(response.content)
