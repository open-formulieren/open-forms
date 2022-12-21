import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings

from freezegun import freeze_time
from privates.test import temp_private_root
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.formio.rendering.registry import register

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
            ("checkbox", "yes"),
            ("currency", "1100000"),
            ("date", "1911-06-29"),
            ("email", "hostmaster@example.org"),
            ("file", "download(2).pdf"),
            ("iban", "NL56 INGB 0705 0051 00"),
            ("licenseplate", "AA-00-13"),
            ("map", "52.193459, 5.279538"),
            ("number", "1"),
            ("password", "Panda1911!"),  # XXX Why is this widget even an option?
            ("phonenumber", "+49 1234 567 890"),
            ("postcode", "3744 AA"),
            ("radio", "Radio number one"),
            ("select", "A fine selection"),
            ("selectboxes", "This; That; The Other"),
            ("signature", SIGNATURE),
            ("textarea", "Largish predetermined ASCII"),
            ("textfield", "Short predetermined ASCII"),
            ("time", "23:50"),
            ("updatenote", "C#"),
        ]
        submission_data = {}
        translations = {}
        components = []

        # carthesian products are big, let's loop to fill these
        for component_type, user_input in fields:
            components.append(
                {
                    "type": component_type,
                    "key": f"{component_type}-key",
                    "label": f"Untranslated {component_type.title()} label",
                    "showInPDF": True,
                    "hidden": False,
                }
            )
            submission_data[f"{component_type}-key"] = user_input
            translations[
                f"Untranslated {component_type.title()} label"
            ] = f"Translated {component_type.title()} label"

        # add radio component options
        radio_component = next(c for c in components if c["type"] == "radio")
        radio_component["values"] = [
            {"label": "Untranslated Radio option one", "value": "radioOne"},
            {"label": "Untranslated Radio option two", "value": "radioTwo"},
        ]
        submission_data[
            radio_component["key"]
        ] = "radioOne"  # value of the selected label
        translations["Untranslated Radio option one"] = "Radio number one"
        translations["Untranslated Radio option two"] = "Translated Radio option two"

        # add select options
        select_component = next(c for c in components if c["type"] == "select")
        select_component["data"] = {
            "values": [
                {"label": "Untranslated Select option one", "value": "selectOne"},
                {"label": "Untranslated Select option two", "value": "selectTwo"},
            ]
        }
        submission_data[
            select_component["key"]
        ] = "selectOne"  # value of the selected label
        translations["Untranslated Select option one"] = "A fine selection"
        translations["Untranslated Select option two"] = "Translated Select option two"

        # add selectbox options
        selectboxes_component = next(
            c for c in components if c["type"] == "selectboxes"
        )
        selectboxes_component["values"] = [
            {
                "label": "Untranslated Selectboxes option one",
                "value": "selectboxesOne",
            },
            {
                "label": "Untranslated Selectboxes option two",
                "value": "selectboxesTwo",
            },
            {
                "label": "Untranslated Selectboxes option three",
                "value": "selectboxesThree",
            },
            {
                "label": "Untranslated Selectboxes option four",
                "value": "selectboxesFour",
            },
        ]
        submission_data[selectboxes_component["key"]] = {
            "selectboxesOne": False,
            "selectboxesTwo": True,
            "selectboxesThree": True,
            "selectboxesFour": True,
        }
        translations["Untranslated Selectboxes option one"] = "The Deal"
        translations["Untranslated Selectboxes option two"] = "This"
        translations["Untranslated Selectboxes option three"] = "That"
        translations["Untranslated Selectboxes option four"] = "The Other"

        # attach file upload
        file_component = next(c for c in components if c["type"] == "file")
        submission_data[file_component["key"]] = [{"originalName": "download(2).pdf"}]

        # fix map coordinates
        map_component = next(c for c in components if c["type"] == "map")
        submission_data[map_component["key"]] = [52.193459, 5.279538]

        # pop the last few components into structural components
        components.extend(
            [
                {
                    "type": "fieldset",
                    "key": "fieldset1",
                    "hidden": False,
                    "label": "Untranslated Field Set label",
                    "components": [components.pop()],
                },
                {
                    "type": "columns",
                    "key": "columns1",
                    "hidden": False,
                    "label": "Untranslated Columns label",
                    "columns": [
                        {
                            "size": 6,
                            "components": [components.pop()],
                        },
                        {
                            "size": 6,
                            "components": [components.pop()],
                        },
                    ],
                },
                {
                    "type": "editgrid",
                    "key": "editgrid1",
                    "hidden": False,
                    "label": "Untranslated Repeating Group label",
                    "groupLabel": "Untranslated Repeating Group Item label",
                    "components": [(grid_child := components.pop())],
                },
            ]
        )
        # adjust path of repeating group
        submission_data["editgrid1"] = [
            {f"{grid_child['type']}-key": submission_data[f"{grid_child['type']}-key"]}
        ]

        translations["Untranslated Field Set label"] = "Translated Field Set label"
        translations[
            "Untranslated Repeating Group label"
        ] = "Translated Repeating Group label"
        translations[
            "Untranslated Repeating Group Item label"
        ] = "Translated Repeating Group Item label"

        report = SubmissionReportFactory(
            submission__language_code="en",
            submission__completed=True,
            submission__form__generate_minimal_setup=True,
            submission__form__translation_enabled=True,
            submission__form__name_en="Translated form name",
            submission__form__formstep__form_definition__name_nl="Walsje",
            submission__form__formstep__form_definition__name_en="A Quickstep",
            submission__form__formstep__form_definition__component_translations={
                "en": translations
            },
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

        # localized date, time and decimal point
        self.assertIn("June 29, 1911", html_report)
        self.assertIn("11:50 p.m.", html_report)
        self.assertIn("1,100,000.00", html_report)

        for component_type, user_input in fields:
            with self.subTest(f"FormIO label for {component_type}"):
                if component_type in ["date", "time", "currency"]:
                    pass  # these are localized
                else:
                    self.assertIn(user_input, html_report)
                self.assertNotIn(
                    f"Untranslated {component_type.title()} label", html_report
                )
                self.assertIn(f"Translated {component_type.title()} label", html_report)

        # assert structural labels
        self.assertIn("Translated Field Set label", html_report)
        self.assertNotIn(
            "Translated Columns label", html_report
        )  # 1451 -> never output a label
        self.assertIn("Translated Repeating Group label", html_report)
        self.assertIn("Translated Repeating Group Item label", html_report)
        self.assertNotIn("Untranslated Field Set label", html_report)
        self.assertNotIn("Untranslated Columns label", html_report)
        self.assertNotIn("Untranslated Repeating Group label", html_report)
        self.assertNotIn("Untranslated Repeating Group Item label", html_report)

        # assert we've tested every component_type ct in register
        plugins = set(ct for ct, _ in register.items())
        plugins.remove("content")  # WYSIWIG seems untranslated in SDK

        tested_plugins = set(ct for ct, _ in fields if ct in plugins)
        # add checked structural "layout" components that don't require
        # user_input and are therefore not in fields
        tested_plugins.update(
            (
                "fieldset",
                "columns",
                "editgrid",
            )
        )
        self.assertEqual(tested_plugins, plugins, "Untested component plugins!")

        # For the lolz, check this again. Fine™ :ok_hand:
        self.assertIn("Panda1911!", html_report)

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


SIGNATURE = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAADkAAAAlCAAAAADdZx65AAAABGdBTUEAALGPC/xhBQAAACBjSFJN"
    "AAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAAmJLR0QA/4ePzL8AAAAHdElN"
    "RQfmDBQODDcI1Lj/AAACGElEQVRIx52VIY/jMBCF988eOGmlI4sXLFipIKSqFBCWEBOTSJaJSUCA"
    "pYCQSCYBIQY2MBsNejrQdtU2btOuWSJ9HvvN85s3/Ha9vUwwx9+Q0fVN6V4iGTz3yoyTtXz8fo6M"
    "Y6+sTwyn/Al8TDIARNsqG9PxR3pGIQZ4sUp2gZ/TNpy2Jadk01OOSXmymwBe2kKM6d5pdkOWPCjV"
    "lNo/uv63XGvLs/wo5g2h067lq5ocTNv2qRu3WhQO+oIkJ1UXAUAsW6SrFAN440GKstbLWfqatshZ"
    "mKNCIRFR/OnZYdNQg+qutHUnYcpNB4sy3HSFiQEcMOQ8eLHqeuUEDyBV8bYtszvvDCbL6U9Ye2gh"
    "THoJ4posAsDBoy25lztX7nO+HUi5iAYA+fMx078EjO+V04VwaCRXnCHJNBQhAHQWXQDA0PtPK75M"
    "NDwRwOAy+1b8Xw4QAB1clJU1ulnMYme+EGuu86+s6D0q9u4Tkj8GEfZ6ZaEiT4qCULOqv4RnCyBe"
    "9YQJCDVzhuS2niHZ0xzvPpUxWzPZUUHzhov8OE0rhcQyO/2AoskOk6d1zbBjdN29c07K2J88uyUH"
    "QPfZxDWdvUrBTGq6mq/snhbdtHaVnRkyVZdCCiGGCH5qltHJ0hxVq3PZyXmSllQDwCKliQ+GxsoJ"
    "ZmA07HSp0kuTN9oE6t9Fzy/O7Fh1vVazeYK7rZnSzajjbBIBAP4DMPDZ6TwbC+0AAAAldEVYdGRh"
    "dGU6Y3JlYXRlADIwMjItMTItMjBUMTQ6MDE6MDUrMDA6MDAHb817AAAAJXRFWHRkYXRlOm1vZGlm"
    "eQAyMDIyLTEyLTIwVDE0OjAwOjU2KzAwOjAw4PgKAAAAAABJRU5ErkJggg=="
)
