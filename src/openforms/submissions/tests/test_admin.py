from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.test import TestCase

from openforms.forms.tests.factories import FormStepFactory

from ..admin import SubmissionAdmin
from ..models import Submission
from .factories import SubmissionFactory, SubmissionStepFactory


class TestSubmissionAdmin(TestCase):
    def test_export(self):
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

        response = SubmissionAdmin(Submission, AdminSite()).export(
            HttpRequest(), Submission.objects.all()
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content,
            b"Formuliernaam,Inzendingdatum,adres,voornaam,familienaam,geboortedatum\r\n"
            b"Form 000,,Voorburg,shea,meyers,\r\n"
            b"Form 000,,,shea,meyers,01-01-1991\r\n",
        )
