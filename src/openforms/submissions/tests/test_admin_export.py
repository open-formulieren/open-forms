from django.urls import reverse
from django.utils import timezone

import tablib
from django_webtest import WebTest
from lxml import etree

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormDefinitionFactory, FormStepFactory
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)


class TestSubmissionExportAdmin(WebTest):
    @classmethod
    def setUpTestData(cls):
        form_definition = FormDefinitionFactory(
            configuration={
                "components": [
                    {"type": "textfield", "key": "adres"},
                    {"type": "textfield", "key": "voornaam"},
                    {"type": "textfield", "key": "familienaam"},
                    {"type": "date", "key": "geboortedatum"},
                    {"type": "signature", "key": "signature"},
                ]
            }
        )
        step = FormStepFactory.create(form_definition=form_definition)
        cls.submission_1 = SubmissionFactory.create(form=step.form)
        submission_2 = SubmissionFactory.create(
            form=step.form, completed_on=timezone.now()
        )
        cls.submission_step_1 = SubmissionStepFactory.create(
            submission=cls.submission_1,
            form_step=step,
            data={"adres": "Voorburg", "voornaam": "shea", "familienaam": "meyers"},
        )
        SubmissionStepFactory.create(
            submission=submission_2,
            form_step=step,
            data={
                "voornaam": "shea",
                "familienaam": "meyers",
                "geboortedatum": "01-01-1991",
            },
        )

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(is_superuser=True, is_staff=True, app=self.app)

    def test_export_csv_successfully_exports_csv_file(self):
        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "export_csv"
        form["_selected_action"] = [
            str(submission.pk) for submission in Submission.objects.all()
        ]

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/csv")
        self.assertEqual(
            response["content-disposition"],
            'attachment; filename="submissions_export.csv"',
        )
        self.assertIsNotNone(response.content)
        # check if it parses
        tablib.Dataset().load(response.content.decode("utf8"), format="csv")

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_export_list.txt"
            ).count(),
            1,
        )

    def test_export_xlsx_successfully_exports_xlsx_file(self):
        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "export_xlsx"
        form["_selected_action"] = [
            str(submission.pk) for submission in Submission.objects.all()
        ]

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["content-type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(
            response["content-disposition"],
            'attachment; filename="submissions_export.xlsx"',
        )
        self.assertIsNotNone(response.content)
        # check if it parses
        tablib.Dataset().load(response.content, format="xlsx")

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_export_list.txt"
            ).count(),
            1,
        )

    def test_export_json_successfully_exports_json_file(self):
        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "export_json"
        form["_selected_action"] = [
            str(submission.pk) for submission in Submission.objects.all()
        ]

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/json")
        self.assertEqual(
            response["content-disposition"],
            'attachment; filename="submissions_export.json"',
        )
        self.assertIsNotNone(response.content)
        # check if it parses
        response.json

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_export_list.txt"
            ).count(),
            1,
        )

    def test_export_xml_successfully_exports_xml_file(self):
        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "export_xml"
        form["_selected_action"] = [
            str(submission.pk) for submission in Submission.objects.all()
        ]

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/xml")
        self.assertEqual(
            response["content-disposition"],
            'attachment; filename="submissions_export.xml"',
        )
        self.assertIsNotNone(response.content)
        # check if it parses
        etree.fromstring(response.content)

        self.assertEqual(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_export_list.txt"
            ).count(),
            1,
        )

    def test_exporting_multiple_forms_fails(self):
        step = FormStepFactory.create()
        SubmissionFactory.create(form=step.form, completed_on=timezone.now())

        response = self.app.get(
            reverse("admin:submissions_submission_changelist"), user=self.user
        )

        form = response.forms["changelist-form"]
        form["action"] = "export_csv"
        form["_selected_action"] = [
            str(submission.pk) for submission in Submission.objects.all()
        ]

        response = form.submit()

        # Assert redirected back to html page
        self.assertEqual(response.status_code, 302)
        response = response.follow()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["content-type"],
            "text/html; charset=utf-8",
        )
        self.assertFalse(
            TimelineLogProxy.objects.filter(
                template="logging/events/submission_export_list.txt"
            ).exists()
        )
