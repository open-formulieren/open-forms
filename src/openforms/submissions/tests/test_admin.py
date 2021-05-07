from unittest.mock import patch

from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from openforms.forms.tests.factories import FormStepFactory

from ..admin import SubmissionAdmin
from ..models import Submission
from .factories import SubmissionFactory, SubmissionStepFactory


class TestSubmissionAdmin(TestCase):
    def setUp(self) -> None:
        step = FormStepFactory.create()
        submission_1 = SubmissionFactory.create(form=step.form)
        submission_2 = SubmissionFactory.create(form=step.form)
        SubmissionStepFactory.create(
            submission=submission_1,
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
        self.submission_admin = SubmissionAdmin(Submission, AdminSite())

    def test_export_csv_successfully_exports_csv_file(self):
        response = self.submission_admin.export_csv(
            HttpRequest(), Submission.objects.all()
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "text/csv")
        self.assertIsNotNone(response.content)

    def test_export_xls_successfully_exports_xls_file(self):
        response = self.submission_admin.export_xls(
            HttpRequest(), Submission.objects.all()
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/vnd.ms-excel")
        self.assertIsNotNone(response.content)

    @patch("openforms.submissions.admin.messages.error")
    def test_exporting_multiple_forms_fails(self, messages_mock):
        step = FormStepFactory.create()
        SubmissionFactory.create(form=step.form)
        request = HttpRequest()

        response = self.submission_admin.export_csv(request, Submission.objects.all())

        self.assertIsNone(response)
        messages_mock.assert_called_once_with(
            request, _("Mag alleen de Submissions van een Form op een keer exporten")
        )
