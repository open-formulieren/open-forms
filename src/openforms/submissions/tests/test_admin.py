from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormStepFactory

from ..models import Submission
from .factories import SubmissionFactory, SubmissionStepFactory


class TestSubmissionAdmin(WebTest):
    @classmethod
    def setUpTestData(cls):
        step = FormStepFactory.create()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)
        cls.submission_1 = SubmissionFactory.create(form=step.form)
        submission_2 = SubmissionFactory.create(form=step.form)
        SubmissionStepFactory.create(
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

    def test_displaying_merged_data(self):
        response = self.app.get(
            reverse(
                "admin:submissions_submission_change", args=(self.submission_1.pk,)
            ),
            user=self.user,
        )

        self.assertInHTML(
            "<li>adres: Voorburg</li>\\n<li>voornaam: shea</li>\\n<li>familienaam: meyers</li>",
            str(response.content),
        )

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

    def test_exporting_multiple_forms_fails(self):
        step = FormStepFactory.create()
        SubmissionFactory.create(form=step.form)

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
