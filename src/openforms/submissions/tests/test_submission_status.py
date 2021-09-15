from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from celery import states
from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory

from ..constants import ProcessingResults, ProcessingStatuses
from ..tokens import submission_status_token_generator
from .factories import SubmissionFactory, SubmissionReportFactory


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


class SubmissionStatusStatusAndResultTests(APITestCase):
    def test_no_task_id_registered(self):
        submission = SubmissionFactory.create(completed=True, on_completion_task_id="")
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["status"], ProcessingStatuses.in_progress)
        self.assertEqual(response_data["paymentUrl"], "")

    def test_in_progress_celery_states(self):
        submission = SubmissionFactory.create(
            completed=True, on_completion_task_id="some-id"
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        in_progress_states = [
            states.PENDING,
            states.RECEIVED,
            states.STARTED,
            states.RETRY,
        ]

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            for state in in_progress_states:
                with self.subTest(celery_state=state):
                    mock_AsyncResult.return_value.state = state

                    response = self.client.get(check_status_url)

                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    response_data = response.json()
                    self.assertEqual(
                        response_data["status"], ProcessingStatuses.in_progress
                    )
                    self.assertEqual(response_data["result"], "")
                    self.assertEqual(response_data["paymentUrl"], "")

    def test_finished_celery_states(self):
        submission = SubmissionFactory.create(
            completed=True, on_completion_task_id="some-id"
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        finished_states = [
            states.SUCCESS,
            states.FAILURE,
        ]

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            for state in finished_states:
                with self.subTest(celery_state=state):
                    mock_AsyncResult.return_value.state = state

                    response = self.client.get(check_status_url)

                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    response_data = response.json()
                    self.assertEqual(response_data["status"], ProcessingStatuses.done)
                    self.assertNotEqual(response_data["result"], "")

    def test_result_for_done_states(self):
        submission = SubmissionFactory.create(
            completed=True, on_completion_task_id="some-id"
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        expected = (
            (states.SUCCESS, ProcessingResults.success),
            (states.FAILURE, ProcessingResults.failed),
            (states.REVOKED, ProcessingResults.retry),
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            for state, expected_result in expected:
                with self.subTest(celery_state=state):
                    mock_AsyncResult.return_value.state = state

                    response = self.client.get(check_status_url)

                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    response_data = response.json()
                    self.assertEqual(response_data["status"], ProcessingStatuses.done)
                    self.assertEqual(response_data["result"], expected_result)
                    # no payment configured
                    self.assertEqual(response_data["paymentUrl"], "")


@temp_private_root()
class SubmissionStatusExtraInformationTests(APITestCase):
    """
    Assert that the extra information fields relay the necessary information.

    Only when the status is 'done' should these fields emit data.
    """

    def test_succesful_processing(self):
        submission = SubmissionFactory.create(
            completed=True,
            on_completion_task_id="some-id",
            form__submission_confirmation_template="You get a cookie!",
            public_registration_reference="OF-ABCDE",
        )
        SubmissionReportFactory.create(submission=submission)
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(check_status_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data["status"], ProcessingStatuses.done)
            self.assertEqual(response_data["result"], ProcessingResults.success)
            self.assertEqual(response_data["publicReference"], "OF-ABCDE")
            self.assertEqual(response_data["errorMessage"], "")
            self.assertEqual(
                response_data["confirmationPageContent"], "You get a cookie!"
            )
            self.assertTrue(
                response_data["reportDownloadUrl"].startswith("http://testserver")
            )
            # no payment configured/required -> no URL
            self.assertEqual(response_data["paymentUrl"], "")

    def test_appointment_user_error(self):
        submission = SubmissionFactory.create(
            completed=True,
            on_completion_task_id="some-id",
            form__submission_confirmation_template="You get a cookie!",
        )
        AppointmentInfoFactory.create(submission=submission, has_missing_info=True)

        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.FAILURE

            response = self.client.get(check_status_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()
            self.assertEqual(response_data["status"], ProcessingStatuses.done)
            self.assertEqual(response_data["result"], ProcessingResults.failed)
            self.assertEqual(response_data["errorMessage"], "Some fields are missing.")
            self.assertEqual(response_data["confirmationPageContent"], "")
            self.assertEqual(response_data["reportDownloadUrl"], "")

    def test_payment_required(self):
        merchant = OgoneMerchantFactory.create()
        submission = SubmissionFactory.create(
            completed=True,
            on_completion_task_id="some-id",
            form__product__price=Decimal("10"),
            form__payment_backend="ogone-legacy",
            # see PR#650 which drops this requirement
            form__payment_backend_options={"merchant_id": merchant.id},
        )
        SubmissionReportFactory.create(submission=submission)
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(check_status_url)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response_data = response.json()

            expected_url = reverse(
                "payments:start",
                kwargs={"uuid": submission.uuid, "plugin_id": "ogone-legacy"},
            )
            self.assertEqual(
                response_data["paymentUrl"], f"http://testserver{expected_url}"
            )
