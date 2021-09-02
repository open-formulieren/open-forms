import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings

from celery.result import AsyncResult
from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse

from openforms.forms.tests.factories import FormFactory

from ..models import SubmissionReport
from ..tasks import generate_submission_report
from ..tokens import token_generator
from .factories import SubmissionFactory, SubmissionReportFactory
from .mixins import SubmissionsMixin


@temp_private_root()
@override_settings(SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS=2)
class DownloadSubmissionReportTests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.form = FormFactory.create(name="Test Form")
        cls.submission = SubmissionFactory.create(form=cls.form)

    def test_valid_token(self):
        self._add_submission_to_session(self.submission)

        submission_report = SubmissionReportFactory.create(
            submission=self.submission, title="Great-Report"
        )
        token = token_generator.make_token(submission_report)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": submission_report.id, "token": token},
        )
        report_status_url = reverse(
            "api:submissions:submission-report-status",
            kwargs={"report_id": submission_report.id, "token": token},
        )

        for url in [report_status_url, download_report_url]:
            with self.subTest(url=url):
                with freeze_time(timedelta(days=1)):
                    response = self.client.get(url)

                    self.assertEqual(status.HTTP_200_OK, response.status_code)

    @patch("celery.app.task.Task.request")
    @patch("openforms.submissions.models.SubmissionReport.get_celery_task")
    def test_get_status(self, mock_result, mock_request):
        self._add_submission_to_session(self.submission)

        submission_report = SubmissionReport.objects.create(
            submission=self.submission, title="Great-Report"
        )
        mock_request.id = 1
        async_result = AsyncResult(id="placeholder")
        async_result._cache = {"status": "SUCCESS"}
        mock_result.return_value = async_result

        generate_submission_report(submission_report.id)
        submission_report.refresh_from_db()

        token = token_generator.make_token(submission_report)

        report_status_url = reverse(
            "api:submissions:submission-report-status",
            kwargs={"report_id": submission_report.id, "token": token},
        )

        response = self.client.get(report_status_url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("SUCCESS", response.json()["status"])

    def test_expired_token(self):
        self._add_submission_to_session(self.submission)

        submission_report = SubmissionReportFactory.create(
            submission=self.submission, title="Great-Report"
        )
        token = token_generator.make_token(submission_report)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": submission_report.id, "token": token},
        )
        report_status_url = reverse(
            "api:submissions:submission-report-status",
            kwargs={"report_id": submission_report.id, "token": token},
        )

        with freeze_time(timedelta(days=3)):
            for url in [report_status_url, download_report_url]:
                response = self.client.get(url)

                self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_token_invalidated_by_earlier_download(self):
        self._add_submission_to_session(self.submission)

        submission_report = SubmissionReportFactory.create(
            submission=self.submission, title="Great-Report"
        )

        token = token_generator.make_token(submission_report)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": submission_report.id, "token": token},
        )
        report_status_url = reverse(
            "api:submissions:submission-report-status",
            kwargs={"report_id": submission_report.id, "token": token},
        )

        response = self.client.get(report_status_url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response = self.client.get(download_report_url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response = self.client.get(download_report_url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

        response = self.client.get(report_status_url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_wrongly_formatted_token(self):
        self._add_submission_to_session(self.submission)

        submission_report = SubmissionReportFactory.create(
            submission=self.submission, title="Great-Report"
        )

        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": submission_report.id, "token": "dummy"},
        )

        response = self.client.get(download_report_url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_invalid_token_timestamp(self):
        self._add_submission_to_session(self.submission)

        submission_report = SubmissionReportFactory.create(
            submission=self.submission, title="Great-Report"
        )

        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": submission_report.id, "token": "$$$-blegh"},
        )

        response = self.client.get(download_report_url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @patch("celery.app.task.Task.request")
    def test_report_generation(self, mock_request):
        self._add_submission_to_session(self.submission)

        submission_report = SubmissionReport.objects.create(
            submission=self.submission, title="Great-Report"
        )
        mock_request.id = 1

        self.assertEqual("", submission_report.task_id)
        self.assertEqual("", submission_report.content.name)

        generate_submission_report(submission_report.id)

        submission_report.refresh_from_db()

        self.assertEqual("1", submission_report.task_id)
        self.assertIn(
            "Test_Form", submission_report.content.name
        )  # report.content.name contains the path too

    @patch("celery.app.task.Task.request")
    @patch(
        "celery.result.AsyncResult._get_task_meta", return_value={"status": "SUCCESS"}
    )
    def test_check_report_status(self, mock_result, mock_request):
        self._add_submission_to_session(self.submission)

        submission_report = SubmissionReport.objects.create(
            submission=self.submission, title="Great-Report"
        )
        mock_request.id = 1

        self.assertIsNone(submission_report.get_celery_task())

        generate_submission_report(submission_report.id)

        submission_report.refresh_from_db()

        self.assertEqual("SUCCESS", submission_report.get_celery_task().status)


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
