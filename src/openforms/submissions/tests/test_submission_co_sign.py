from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from .factories import SubmissionFactory
from .mixins import SubmissionsMixin


class SubmissionCoSignStatusTests(SubmissionsMixin, APITestCase):
    def test_submission_id_not_in_session(self):
        submission = SubmissionFactory.create(co_sign_data={})
        endpoint = reverse("api:submission-co-sign", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_submission_co_sign_status(self):
        """
        Assert that the identifier is not present in the API response.
        """
        submission = SubmissionFactory.create(co_sign_data={})
        self._add_submission_to_session(submission)
        endpoint = reverse("api:submission-co-sign", kwargs={"uuid": submission.uuid})

        response = self.client.get(endpoint)

        self.assertEqual(
            response.json(),
            {
                "coSigned": True,
                "fields": {
                    "firstName": "Bono",
                    "lastName": "My Tires",
                },
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
                "fields": {},
            },
        )
