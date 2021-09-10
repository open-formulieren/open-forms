from datetime import timedelta

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..tokens import submission_status_token_generator
from .factories import SubmissionFactory


class SubmissionStatusPermissionTests(APITestCase):
    def test_valid_token(self):
        # Use empty task ID to not need a real broker
        submission = SubmissionFactory.create(completed=True, on_completion_task_id="")
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with freeze_time(timedelta(days=1)):
            response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expired_token(self):
        # Use empty task ID to not need a real broker
        submission = SubmissionFactory.create(completed=True, on_completion_task_id="")
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with freeze_time(timedelta(days=2)):
            response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_invalidated_by_other_processing_run(self):
        submission = SubmissionFactory.create(completed=True, on_completion_task_id="")
        old_token = submission_status_token_generator.make_token(submission)
        submission.on_completion_task_id = "some-id"
        submission.save()
        check_status_url = reverse(
            "api:submission-status",
            kwargs={"uuid": submission.uuid, "token": old_token},
        )

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrongly_formatted_token(self):
        submission = SubmissionFactory.create(completed=True, on_completion_task_id="")
        # can't reverse because bad format lol
        check_status_url = f"/api/v1/submissions/{submission.uuid}/badformat/status"

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_token_timestamp(self):
        submission = SubmissionFactory.create(completed=True, on_completion_task_id="")
        # can't reverse because bad format lol
        check_status_url = f"/api/v1/submissions/{submission.uuid}/$$$-{'a'*20}/status"

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
