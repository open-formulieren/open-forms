import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings

from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)

from ..models import SubmissionReport
from ..tasks import generate_submission_report
from ..tokens import submission_report_token_generator
from .factories import SubmissionFactory, SubmissionReportFactory, SubmissionStepFactory


@temp_private_root()
@override_settings(SUBMISSION_REPORT_URL_TOKEN_TIMEOUT_DAYS=2)
class DownloadSubmissionReportTests(APITestCase):
    def test_valid_token(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        token = submission_report_token_generator.make_token(report)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )

        with freeze_time(timedelta(days=1)):
            response = self.client.get(download_report_url)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_expired_token(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        token = submission_report_token_generator.make_token(report)
        download_report_url = reverse(
            "api:submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )

        with freeze_time(timedelta(days=3)):
            response = self.client.get(download_report_url)

            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_token_invalidated_by_earlier_download(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        token = submission_report_token_generator.make_token(report)
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
        submission = SubmissionFactory.create(completed=True, form__name="Test Form")
        mock_request.id = "some-id"

        generate_submission_report(submission.id)

        report = submission.report
        self.assertEqual("some-id", report.task_id)
        # report.content.name contains the path too
        self.assertTrue(report.content.name.endswith("Test_Form.pdf"))

    @override_settings(LANGUAGE_CODE="nl")
    def test_submission_printable_data(self):
        form = FormFactory.create()
        form_def = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {
                        "key": "radio1",
                        "type": "radio",
                        "label": "Test Radio",
                        "values": [
                            {"label": "Test Option 1", "value": "testOption1"},
                            {"label": "Test Option 2", "value": "testOption2"},
                        ],
                    },
                    {
                        "key": "select1",
                        "type": "select",
                        "label": "Test Select",
                        "data": {
                            "values": [
                                {"label": "Test Option 1", "value": "testOption1"},
                                {"label": "Test Option 2", "value": "testOption2"},
                            ]
                        },
                    },
                    {
                        "key": "date0",
                        "type": "date",
                        "label": "Test date 0",
                    },
                    {
                        "key": "date1",
                        "type": "date",
                        "label": "Test date 1",
                    },
                    {
                        "key": "date2",
                        "type": "date",
                        "label": "Test date 2",
                        "multiple": True,
                    },
                    {
                        "key": "time0",
                        "type": "time",
                        "label": "Test time 1",
                    },
                    # appointment fields are special...
                    {
                        "key": "date3",
                        "type": "select",
                        "label": "Afspraakdatum",
                        "appointments": {
                            "showDates": True,
                        },
                    },
                    {
                        "key": "time1",
                        "type": "select",
                        "label": "Afspraaktijdstip",
                        "appointments": {
                            "showTimes": True,
                        },
                    },
                    {
                        "key": "number1",
                        "type": "number",
                        "label": "Test number 1",
                        "decimalLimit": 0,
                    },
                    {
                        "key": "number2",
                        "type": "number",
                        "label": "Test number 2",
                        "decimalLimit": 2,
                    },
                    {
                        "key": "currency",
                        "type": "currency",
                        "label": "Test currency",
                    },
                ]
            }
        )
        form_step = FormStepFactory.create(form_definition=form_def, form=form)
        submission = SubmissionFactory.create(completed=True, form=form)
        SubmissionStepFactory.create(
            data={
                "radio1": "testOption1",
                "select1": "testOption2",
                "date1": "2022-01-02",
                "date2": ["2022-01-02", "2022-02-03"],
                "time0": "17:30:00",
                "date3": "2021-12-24",
                "time1": "2021-12-24T08:10:00+01:00",
                "number1": 1,
                "number2": 1.23,
                "currency": 1.23,
            },
            submission=submission,
            form_step=form_step,
        )

        printable_data = submission.get_printable_data()

        values = [
            ("Test Radio", "Test Option 1"),
            ("Test Select", "Test Option 2"),
            ("Test date 1", "2 januari 2022"),
            ("Test date 2", "2 januari 2022, 3 februari 2022"),
            ("Test time 1", "17:30"),
            ("Afspraakdatum", "24 december 2021"),
            ("Afspraaktijdstip", "08:10"),
            ("Test number 1", "1"),
            ("Test number 2", "1,23"),
            ("Test currency", "1,23"),
        ]
        for label, value in values:
            with self.subTest(label):
                self.assertIn(label, printable_data)
                self.assertEqual(value, printable_data[label])

        not_values = [
            "Test date 0",
        ]
        for label in not_values:
            with self.subTest(label):
                self.assertNotIn(label, printable_data)

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
