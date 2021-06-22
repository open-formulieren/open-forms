import os
from datetime import timedelta

from django.test import TestCase, override_settings

from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionReportFactory,
)
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.submissions.tokens import token_generator
from openforms.submissions.utils import create_submission_report


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

        submission_report = create_submission_report(self.submission)
        token = token_generator.make_token(submission_report)
        download_report_url = reverse(
            "submission:download-submission",
            kwargs={"report_id": submission_report.id, "token": token},
        )

        for day in range(2):
            with self.subTest(day_offset=day):
                with freeze_time(timedelta(days=day)):
                    response = self.client.get(download_report_url)

                    self.assertTrue(status.HTTP_200_OK, response.status_code)

    def test_expired_token(self):
        self._add_submission_to_session(self.submission)

        submission_report = create_submission_report(self.submission)
        token = token_generator.make_token(submission_report)
        download_report_url = reverse(
            "submission:download-submission",
            kwargs={"report_id": submission_report.id, "token": token},
        )

        with freeze_time(timedelta(days=3)):
            response = self.client.get(download_report_url)

            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_token_invalidated_by_earlier_download(self):
        self._add_submission_to_session(self.submission)

        submission_report = create_submission_report(self.submission)
        token = token_generator.make_token(submission_report)
        download_report_url = reverse(
            "submission:download-submission",
            kwargs={"report_id": submission_report.id, "token": token},
        )

        response = self.client.get(download_report_url)

        self.assertTrue(status.HTTP_200_OK, response.status_code)

        response = self.client.get(download_report_url)

        self.assertTrue(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_wrongly_formatted_token(self):
        self._add_submission_to_session(self.submission)

        submission_report = create_submission_report(self.submission)
        download_report_url = reverse(
            "submission:download-submission",
            kwargs={"report_id": submission_report.id, "token": "dummy"},
        )

        response = self.client.get(download_report_url)

        self.assertTrue(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_invalid_token_timestamp(self):
        self._add_submission_to_session(self.submission)

        submission_report = create_submission_report(self.submission)
        download_report_url = reverse(
            "submission:download-submission",
            kwargs={"report_id": submission_report.id, "token": "$$$-blegh"},
        )

        response = self.client.get(download_report_url)

        self.assertTrue(status.HTTP_403_FORBIDDEN, response.status_code)


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
