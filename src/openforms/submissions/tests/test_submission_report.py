import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings

from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse

from ..models import SubmissionReport
from ..tasks import generate_submission_report
from ..tokens import token_generator
from .factories import SubmissionFactory, SubmissionReportFactory


@temp_private_root()
@override_settings(SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS=2)
class DownloadSubmissionReportTests(TestCase):
    def test_valid_token(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        token = token_generator.make_token(report)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )

        with freeze_time(timedelta(days=1)):
            response = self.client.get(download_report_url)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_expired_token(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        token = token_generator.make_token(report)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )

        with freeze_time(timedelta(days=3)):
            response = self.client.get(download_report_url)

            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_token_invalidated_by_earlier_download(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        token = token_generator.make_token(report)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )

        with self.subTest("First download"):
            response = self.client.get(download_report_url)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

        with self.subTest("Second download"):
            response = self.client.get(download_report_url)

            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_wrongly_formatted_token(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": report.id, "token": "dummy"},
        )

        response = self.client.get(download_report_url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_invalid_token_timestamp(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": report.id, "token": "$$$-blegh"},
        )

        response = self.client.get(download_report_url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @patch("celery.app.task.Task.request")
    def test_report_generation(self, mock_request):
        submission = SubmissionFactory.create(
            completed=True, form__public_name="Test Form"
        )
        mock_request.id = "some-id"

        generate_submission_report(submission.id)

        report = submission.report
        self.assertEqual("some-id", report.task_id)
        # report.content.name contains the path too
        self.assertTrue(report.content.name.endswith("Test_Form.pdf"))

    @patch(
        "celery.result.AsyncResult._get_task_meta", return_value={"status": "SUCCESS"}
    )
    def test_check_report_status(self, mock_result):
        submission = SubmissionFactory.create(completed=True)
        submission_report = SubmissionReportFactory.create(submission=submission)

        with self.subTest("without celery task ID stored"):
            self.assertIsNone(submission_report.get_celery_task())

        submission_report.task_id = "some-id"
        with self.subTest("with celery task ID stored"):
            task_result = submission_report.get_celery_task()
            self.assertEqual(task_result.status, "SUCCESS")

    @patch("celery.app.task.Task.request")
    def test_celery_task_id_stored(self, mock_request):
        # monkeypatch the celery task ID onto the request
        submission = SubmissionFactory.create(completed=True)
        mock_request.id = "some-id"

        generate_submission_report(submission.id)

        report = submission.report
        self.assertEqual(report.task_id, "some-id")

    @patch("celery.app.task.Task.request")
    def test_task_idempotency(self, mock_request):
        mock_request.id = "other-id"
        report = SubmissionReportFactory.create(
            submission__completed=True, task_id="some-id"
        )

        generate_submission_report(report.submission_id)

        report.refresh_from_db()
        self.assertEqual(report.task_id, "some-id")
        self.assertEqual(SubmissionReport.objects.count(), 1)


@temp_private_root()
class DeleteReportTests(TestCase):
    def test_file_deletion(self):
        submission_report = SubmissionReportFactory.create()

        file_path = submission_report.content.path

        self.assertTrue(os.path.exists(file_path))

        submission_report.delete()

        self.assertFalse(os.path.exists(file_path))

    def test_file_deleted_on_submission_deletion(self):
        submission_report = SubmissionReportFactory.create()

        file_path = submission_report.content.path

        self.assertTrue(os.path.exists(file_path))

        submission_report.submission.delete()

        self.assertFalse(os.path.exists(file_path))
