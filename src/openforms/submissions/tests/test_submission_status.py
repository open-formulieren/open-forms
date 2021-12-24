from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from celery import states
from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.appointments.tests.factories import AppointmentInfoFactory
from openforms.payments.constants import PaymentStatus
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory
from openforms.payments.tests.factories import SubmissionPaymentFactory

from ..constants import SUBMISSIONS_SESSION_KEY, ProcessingResults, ProcessingStatuses
from ..tasks import cleanup_on_completion_results
from ..tokens import submission_status_token_generator
from .factories import SubmissionFactory, SubmissionReportFactory


class SubmissionStatusPermissionTests(APITestCase):
    def test_valid_token(self):
        # Use empty task ID to not need a real broker
        submission = SubmissionFactory.create(completed=True, on_completion_task_ids=[])
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with freeze_time(timedelta(days=1)):
            response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expired_token(self):
        # Use empty task ID to not need a real broker
        submission = SubmissionFactory.create(completed=True, on_completion_task_ids=[])
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with freeze_time(timedelta(days=2)):
            response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_invalidated_by_new_completion(self):
        submission = SubmissionFactory.create(completed=True, on_completion_task_ids=[])
        old_token = submission_status_token_generator.make_token(submission)
        submission.completed_on = timezone.now()
        submission.save()
        check_status_url = reverse(
            "api:submission-status",
            kwargs={"uuid": submission.uuid, "token": old_token},
        )

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrongly_formatted_token(self):
        submission = SubmissionFactory.create(completed=True, on_completion_task_ids=[])
        # can't reverse because bad format lol
        check_status_url = f"/api/v1/submissions/{submission.uuid}/badformat/status"

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_token_timestamp(self):
        submission = SubmissionFactory.create(completed=True, on_completion_task_ids=[])
        # can't reverse because bad format lol
        check_status_url = f"/api/v1/submissions/{submission.uuid}/$$$-{'a'*20}/status"

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SubmissionStatusStatusAndResultTests(APITestCase):
    def test_no_task_id_registered(self):
        submission = SubmissionFactory.create(completed=True, on_completion_task_ids=[])
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        response = self.client.get(check_status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["status"], ProcessingStatuses.in_progress)
        self.assertEqual(response_data["paymentUrl"], "")
        self.assertEqual(response_data["reportDownloadUrl"], "")
        self.assertEqual(response_data["confirmationPageContent"], "")

    def test_in_progress_celery_states(self):
        submission = SubmissionFactory.create(
            completed=True, on_completion_task_ids=["some-id"]
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
            completed=True, on_completion_task_ids=["some-id"]
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
            completed=True, on_completion_task_ids=["some-id"]
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        expected = (
            (states.SUCCESS, ProcessingResults.success),
            (states.FAILURE, ProcessingResults.failed),
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

    def test_submission_id_in_session_for_failed_result(self):
        submission = SubmissionFactory.create(
            completed=True, on_completion_task_ids=["some-id"]
        )
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
            # check that the submission ID is in the session
            self.assertEqual(
                response.wsgi_request.session[SUBMISSIONS_SESSION_KEY],
                [str(submission.uuid)],
            )


@temp_private_root()
class SubmissionStatusExtraInformationTests(APITestCase):
    """
    Assert that the extra information fields relay the necessary information.

    Only when the status is 'done' should these fields emit data.
    """

    def test_succesful_processing(self):
        submission = SubmissionFactory.create(
            completed=True,
            on_completion_task_ids=["some-id"],
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
            on_completion_task_ids=["some-id"],
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
            on_completion_task_ids=["some-id"],
            form__product__price=Decimal("10"),
            form__payment_backend="ogone-legacy",
            # see PR#650 which drops this requirement
            form__payment_backend_options={"merchant_id": merchant.id},
        )
        submission.calculate_price()
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

    def test_payment_already_received(self):
        submission = SubmissionFactory.create(
            completed=True,
            on_completion_task_ids=["some-id"],
            public_registration_reference="OF-ABCDE",
            form__product__price=Decimal("12.34"),
            form__payment_backend="test",
        )
        SubmissionPaymentFactory.for_submission(
            submission, status=PaymentStatus.completed
        )
        token = submission_status_token_generator.make_token(submission)
        check_status_url = reverse(
            "api:submission-status", kwargs={"uuid": submission.uuid, "token": token}
        )

        with patch("openforms.submissions.status.AsyncResult") as mock_AsyncResult:
            mock_AsyncResult.return_value.state = states.SUCCESS

            response = self.client.get(check_status_url)
            response_data = response.json()

            # Payment is required, but has already been done -> No URL
            self.assertEqual(response_data["paymentUrl"], "")


@patch("openforms.submissions.status.AsyncResult.forget", return_value=None)
class CleanupTaskTests(TestCase):
    def test_incomplete_submission(self, mock_forget):
        SubmissionFactory.create(
            completed=False,
            suspended_on=None,
            on_completion_task_ids=["some-id"],
        )

        cleanup_on_completion_results()

        mock_forget.assert_not_called()

    def test_complete_but_too_young(self, mock_forget):
        SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(seconds=10),
            suspended_on=None,
            on_completion_task_ids=["some-id"],
        )

        cleanup_on_completion_results()

        mock_forget.assert_not_called()

    def test_suspended(self, mock_forget):
        SubmissionFactory.create(
            completed=False,
            suspended_on=timezone.now() - timedelta(seconds=10),
            on_completion_task_ids=[],
        )

        cleanup_on_completion_results()

        mock_forget.assert_not_called()

    def test_completed_and_old_enough(self, mock_forget):
        submission = SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(days=2, seconds=10),
            suspended_on=None,
            on_completion_task_ids=["some-id"],
        )

        cleanup_on_completion_results()

        mock_forget.assert_called_once_with()
        submission.refresh_from_db()
        self.assertEqual(submission.on_completion_task_ids, [])

    def test_multiple_cleanup_calls_only_forget_once(self, mock_forget):
        SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(days=2, seconds=10),
            suspended_on=None,
            on_completion_task_ids=["some-id"],
        )

        cleanup_on_completion_results()
        cleanup_on_completion_results()

        mock_forget.assert_called_once_with()

    def test_cleanup_skips_completed_submissions_without_tasks(self, mock_forget):
        SubmissionFactory.create(
            completed=True,
            completed_on=timezone.now() - timedelta(days=2, seconds=10),
            suspended_on=None,
            on_completion_task_ids=[],
        )

        cleanup_on_completion_results()

        mock_forget.assert_not_called()
