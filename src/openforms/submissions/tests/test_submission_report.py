import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings

from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

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

    def test_token_not_invalidated_by_earlier_download(self):
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

            self.assertEqual(status.HTTP_200_OK, response.status_code)

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

    def test_report_is_generated_in_same_language_as_submission(self):
        # fixture_data
        fields = [
            # Component.type, user_input
            ("bsn", "111222333"),
            ("date", "1911-06-29"),
            ("email", "hostmaster@example.org"),
            # ("file", ""),
            ("iban", "NL56 INGB 0705 0051 00"),
            ("licenseplate", "AA-00-13"),
            ("number", "1"),
            ("password", "Panda1911!"),
            ("phoneNumber", "+49 1234 567 890"),
            ("postcode", "3744 AA"),
            # ("radio", ""),
            # ("select", ""),
            # ("selectboxes", ""),
            ("textarea", "Predetermined largish ASCII"),
            ("textfield", "Short predetermined ASCII"),
            ("time", "23:50"),
        ]
        submission_data = {}
        component_translations = {"en": {}}
        components = []

        # carthesian products are big, let's loop to fill these
        for i, (component_type, user_input) in enumerate(fields):
            components.append(
                {
                    "type": component_type,
                    "key": f"key{i}",
                    "label": f"Untranslated {component_type.title()} label",
                    "showInPDF": True,
                    "hidden": False,
                }
            )
            submission_data[f"key{i}"] = user_input
            component_translations["en"][
                f"Untranslated {component_type.title()} label"
            ] = f"Translated {component_type.title()} label"

        report = SubmissionReportFactory(
            submission__language_code="en",
            submission__completed=True,
            submission__form__generate_minimal_setup=True,
            submission__form__translation_enabled=True,
            submission__form__name_en="Translated form name",
            # One form step for mankind…
            submission__form__formstep__form_definition__name_nl="Walsje",
            submission__form__formstep__form_definition__name_en="A Quickstep",
            submission__form__formstep__form_definition__component_translations=component_translations,
            submission__form__formstep__form_definition__configuration={
                "components": components,
            },
        )
        SubmissionStepFactory.create(
            submission=report.submission,
            form_step=report.submission.form.formstep_set.get(),
            data=submission_data,
        )

        # create report
        html_report = report.generate_submission_report_pdf()

        self.assertIn("Translated form name", html_report)
        self.assertIn("A Quickstep", html_report)
        self.assertNotIn("Walsje", html_report)

        # localized date and time
        self.assertIn("June 29, 1911", html_report)
        self.assertIn("11:50 p.m.", html_report)

        for component_type, value in fields:
            with self.subTest(f"FormIO label for {component_type}"):
                if component_type in ["date", "time"]:
                    pass  # these are localized
                else:
                    self.assertIn(value, html_report)
                self.assertNotIn(
                    f"Untranslated {component_type.title()} label", html_report
                )
                self.assertIn(f"Translated {component_type.title()} label", html_report)

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
