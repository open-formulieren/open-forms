import json
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
            "submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )

        with freeze_time(timedelta(days=1)):
            response = self.client.get(download_report_url)

            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_download_response(self):
        report = SubmissionReportFactory.create(
            submission__completed=True, content__filename="report.pdf"
        )
        token = submission_report_token_generator.make_token(report)
        download_report_url = reverse(
            "submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )

        response = self.client.get(download_report_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(
            response["Content-Disposition"], 'attachment; filename="report.pdf"'
        )

    def test_expired_token(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        token = submission_report_token_generator.make_token(report)
        download_report_url = reverse(
            "submissions:download-submission",
            kwargs={"report_id": report.id, "token": token},
        )

        with freeze_time(timedelta(days=3)):
            response = self.client.get(download_report_url)

            self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_token_not_invalidated_by_earlier_download(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        token = submission_report_token_generator.make_token(report)
        download_report_url = reverse(
            "submissions:download-submission",
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
            "submissions:download-submission",
            kwargs={"report_id": report.id, "token": "dummy"},
        )

        response = self.client.get(download_report_url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_invalid_token_timestamp(self):
        report = SubmissionReportFactory.create(submission__completed=True)
        download_report_url = reverse(
            "submissions:download-submission",
            kwargs={"report_id": report.id, "token": "$$$-blegh"},
        )

        response = self.client.get(download_report_url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @patch("celery.app.task.Task.request")
    def test_report_generation(self, mock_request):
        submission = SubmissionFactory.create(
            completed=True, form__name="Test Form", form__slug="test-form"
        )
        mock_request.id = "some-id"

        generate_submission_report(submission.id)

        report = submission.report
        self.assertEqual("some-id", report.task_id)
        # report.content.name contains the path too
        self.assertTrue(report.content.name.endswith("test-form.pdf"))

    def test_report_is_generated_in_same_language_as_submission(self):
        # fixture_data
        fields = [
            # Component.type, localised submitted values
            ("bsn", "111222333"),
            ("checkbox", "yes"),
            ("currency", "1,100,000"),  # 1100000
            ("date", "June 29, 1911"),  # 1922-06-29
            ("email", "hostmaster@example.org"),
            ("file", "download(2).pdf"),
            ("iban", "NL56 INGB 0705 0051 00"),
            ("licenseplate", "AA-00-13"),
            ("map", "52.193459, 5.279538"),
            ("number", "1"),
            (
                "partners",
                '[{"bsn": "999970136", "firstNames": "Pia", "initials": "P.", "affixes": "", "lastName": "Pauw", "dateOfBirth": "April 1, 1989", "dateOfBirthPrecision": "date"}]',
            ),
            ("password", "Panda1911!"),  # XXX Why is this widget even an option?
            ("phonenumber", "+49 1234 567 890"),
            ("postcode", "3744 AA"),
            ("radio", "Radio number one"),
            ("select", "A fine selection"),
            ("selectboxes", "<ul><li>This</li><li>That</li><li>The Other</li></ul>"),
            ("signature", SIGNATURE),
            ("textarea", "Largish predetermined ASCII"),
            ("textfield", "Short predetermined ASCII"),
            ("time", "11:50 p.m."),  # 23:50
            ("updatenote", "C#"),
        ]

        components = []  # FormDefiniton

        for component_type, _ in fields:
            # common base
            component = {
                "type": component_type,
                "key": f"{component_type}key",
                "label": f"Untranslated {component_type.title()} label",
                "showInPDF": True,
                "hidden": False,
                "openForms": {
                    "translations": {
                        "en": {"label": f"Translated {component_type.title()} label"},
                        "nl": {"label": f"Untranslated {component_type.title()} label"},
                    }
                },
            }

            # add the component to the FormDefintion
            components.append(component)

            # but massage the weirder components into shape
            match component:
                case {"type": "radio"}:
                    component["values"] = [
                        {
                            "label": "Untranslated Radio option one",
                            "value": "radioOne",
                            "openForms": {
                                "translations": {
                                    "en": {"label": "Radio number one"},
                                    "nl": {"label": "Untranslated Radio option one"},
                                }
                            },
                        },
                        {
                            "label": "Untranslated Radio option two",
                            "value": "radioTwo",
                            "openForms": {
                                "translations": {
                                    "en": {"label": "Radio number two"},
                                    "nl": {"label": "Untranslated Radio option two"},
                                }
                            },
                        },
                    ]
                case {"type": "select"}:
                    component["data"] = {
                        "values": [
                            {
                                "label": "Untranslated Select option one",
                                "value": "selectOne",
                                "openForms": {
                                    "translations": {
                                        "en": {"label": "A fine selection"},
                                        "nl": {
                                            "label": "Untranslated Select option one"
                                        },
                                    }
                                },
                            },
                            {
                                "label": "Untranslated Select option two",
                                "value": "selectTwo",
                                "openForms": {
                                    "translations": {
                                        "en": {"label": "Translated Select option two"},
                                        "nl": {
                                            "label": "Untranslated Select option two"
                                        },
                                    }
                                },
                            },
                        ]
                    }
                case {"type": "selectboxes"}:
                    component["values"] = [
                        {
                            "label": "Untranslated Selectboxes option one",
                            "value": "selectboxesOne",
                            "openForms": {
                                "translations": {
                                    "en": {"label": "The Deal"},
                                    "nl": {
                                        "label": "Untranslated Selectboxes option one"
                                    },
                                }
                            },
                        },
                        {
                            "label": "Untranslated Selectboxes option two",
                            "value": "selectboxesTwo",
                            "openForms": {
                                "translations": {
                                    "en": {"label": "This"},
                                    "nl": {
                                        "label": "Untranslated Selectboxes option two"
                                    },
                                }
                            },
                        },
                        {
                            "label": "Untranslated Selectboxes option three",
                            "value": "selectboxesThree",
                            "openForms": {
                                "translations": {
                                    "en": {"label": "That"},
                                    "nl": {
                                        "label": "Untranslated Selectboxes option three"
                                    },
                                }
                            },
                        },
                        {
                            "label": "Untranslated Selectboxes option four",
                            "value": "selectboxesFour",
                            "openForms": {
                                "translations": {
                                    "en": {"label": "The Other"},
                                    "nl": {
                                        "label": "Untranslated Selectboxes option four"
                                    },
                                }
                            },
                        },
                    ]

        # pop the last few components into structural components
        components.extend(
            [
                {
                    "type": "fieldset",
                    "key": "fieldset1",
                    "hidden": False,
                    "label": "Untranslated Field Set label",
                    "components": [components.pop()],
                    "openForms": {
                        "translations": {
                            "en": {"label": "Translated Field Set label"},
                            "nl": {"label": "Untranslated Field Set label"},
                        }
                    },
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
                    "openForms": {
                        "translations": {
                            "en": {"label": "Translated Columns label"},
                            "nl": {"label": "Untranslated Columns label"},
                        }
                    },
                },
                {
                    "type": "editgrid",
                    "key": "editgrid1",
                    "hidden": False,
                    "label": "Untranslated Repeating Group label",
                    "groupLabel": "Untranslated Repeating Group Item label",
                    "components": [components.pop()],
                    "openForms": {
                        "translations": {
                            "en": {
                                "label": "Translated Repeating Group label",
                                "groupLabel": "Translated Repeating Group Item label",
                            },
                            "nl": {
                                "label": "Untranslated Repeating Group label",
                                "groupLabel": "Untranslated Repeating Group Item label",
                            },
                        }
                    },
                },
                {
                    "type": "checkbox",
                    "key": "interpolkey",
                    "hidden": False,
                    "label": "Untranslated label using {{textfieldkey}} interpolation",
                    "openForms": {
                        "translations": {
                            "en": {"label": "Interpolated {{textfieldkey}} label"},
                            "nl": {
                                "label": "Untranslated label using {{textfieldkey}} interpolation"
                            },
                        }
                    },
                },
            ]
        )
        report = SubmissionReportFactory(
            submission__language_code="en",
            submission__completed=True,
            submission__form__generate_minimal_setup=True,
            submission__form__translation_enabled=True,
            submission__form__name_nl="Untranslated Form name",
            submission__form__name_en="Translated Form name",
            submission__form__formstep__form_definition__name_nl="Untranslated Form Step name",
            submission__form__formstep__form_definition__name_en="A Quickstep",
            submission__form__formstep__form_definition__configuration={
                "components": components,
            },
        )
        SubmissionStepFactory.create(
            submission=report.submission,
            form_step=report.submission.form.formstep_set.get(),
            data={
                "bsnkey": "111222333",
                "checkboxkey": True,
                "currencykey": "1100000",
                "datekey": "1911-06-29",
                "editgrid1": [{"textareakey": "Largish predetermined ASCII"}],
                "emailkey": "hostmaster@example.org",
                "filekey": [{"originalName": "download(2).pdf"}],
                "ibankey": "NL56 INGB 0705 0051 00",
                "licenseplatekey": "AA-00-13",
                "mapkey": {
                    "type": "Point",
                    "coordinates": [52.193459, 5.279538],
                },
                "numberkey": "1",
                "partnerskey": [
                    {
                        "bsn": "999970136",
                        "firstNames": "Pia",
                        "initials": "P.",
                        "affixes": "",
                        "lastName": "Pauw",
                        "dateOfBirth": "1989-04-01",
                        "dateOfBirthPrecision": "date",
                    }
                ],
                "passwordkey": "Panda1911!",
                "phonenumberkey": "+49 1234 567 890",
                "postcodekey": "3744 AA",
                "radiokey": "radioOne",
                "selectkey": "selectOne",
                "selectboxeskey": {
                    "selectboxesFour": True,
                    "selectboxesOne": False,
                    "selectboxesThree": True,
                    "selectboxesTwo": True,
                },
                "signaturekey": SIGNATURE,
                "textareakey": "Largish predetermined ASCII",
                "textfieldkey": "Short predetermined ASCII",
                "timekey": "23:50",
                "updatenotekey": "C#",
                "interpolkey": True,
            },
        )

        # create report
        html_report = report.generate_submission_report_pdf()

        self.assertIn("Translated Form name", html_report)
        self.assertIn("A Quickstep", html_report)

        for component_type, localised_input in fields:
            with self.subTest(f"FormIO label for {component_type}"):
                if component_type != "partners":
                    self.assertIn(localised_input, html_report)

                self.assertNotIn(
                    f"Untranslated {component_type.title()} label", html_report
                )
                self.assertIn(f"Translated {component_type.title()} label", html_report)

            # Partners component tests
            if component_type == "partners":
                partners_list = json.loads(localised_input)
                del partners_list[0]["firstNames"]
                del partners_list[0]["dateOfBirthPrecision"]
                for partner_label, partner_value in partners_list[0].items():
                    self.assertIn(partner_label, html_report)
                    self.assertIn(partner_value, html_report)

        # assert structural labels
        self.assertIn("Translated Field Set label", html_report)
        self.assertIn("Translated Repeating Group label", html_report)
        self.assertIn("Translated Repeating Group Item label", html_report)
        # 1451 -> never output a label
        self.assertNotIn("Translated Columns label", html_report)

        self.assertIn("Interpolated Short predetermined ASCII label", html_report)
        # Assert nothing was left untranslated
        self.assertNotIn("Untranslated", html_report)

        # assert we've tested every component_type ct in register
        plugins = set(ct for ct, _ in register.items())
        # WYSIWIG seems untranslated in SDK TODO after/in issue #2475
        plugins.remove("content")
        # soft-required errors are not shown in PDF report
        plugins.remove("softRequiredErrors")

        tested_plugins = set(ct for ct, _ in fields if ct in plugins)
        # add checked structural "layout" components that don't require
        # user input and are therefore not in fields
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
