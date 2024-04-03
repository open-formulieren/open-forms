from unittest.mock import patch

from django.test import RequestFactory, TestCase, override_settings, tag
from django.utils.html import escape

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.submissions.dev_views import SubmissionPDFTestView
from openforms.submissions.tests.factories import SubmissionFactory

from ..contrib.demo.plugin import DemoAppointment
from .factories import AppointmentFactory, AppointmentProductFactory


class PDFGenerationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        appointment = AppointmentFactory.create(
            plugin="demo",
            submission__language_code="nl",
            submission__registration_success=True,
            submission__with_report=True,
            appointment_info__registration_ok=True,
            appointment_info__appointment_id="a-remote-id",
            location__identifier="1",
        )
        AppointmentProductFactory.create(
            appointment=appointment, product_id="1", amount=1
        )
        cls.submission = appointment.submission

    def test_appointment_info_is_included(self):
        # NB the demo plugin appointment info is hardcoded in the plugin
        html = self.submission.report.generate_submission_report_pdf()

        self.assertIn("Afspraakinformatie", html)
        self.assertIn("Test product 1", html)
        self.assertIn("Test location", html)
        self.assertIn("Test address", html)
        self.assertIn("Datum en tijd", html)

        self.assertIn(escape("<h1>Data</h1>"), html)

    @override_settings(DEBUG=True)
    def test_appointment_info_is_included_in_submission_pdf_test_view(self):
        # We're too late for django.urls.reverse to work; use the view
        view = SubmissionPDFTestView.as_view()
        request = RequestFactory().get("/foo")
        request.user = SuperUserFactory()
        response = view(request, pk=self.submission.id)

        self.assertContains(response, "Afspraakinformatie")
        self.assertContains(response, "Test product 1")
        self.assertContains(response, "Test location")
        self.assertContains(response, "Datum en tijd")

    def test_submission_without_appointment_shows_no_appointment_info(self):
        submission = SubmissionFactory.create(
            language_code="nl",
            registration_success=True,
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()

        self.assertNotIn("Afspraakinformatie", html)

    @tag("gh-4103")
    def test_uses_remote_appoinment_id(self):
        plugin = DemoAppointment("demo")

        with (
            patch("openforms.appointments.renderer.get_plugin", return_value=plugin),
            patch.object(
                plugin, "get_appointment_details", wraps=plugin.get_appointment_details
            ) as m_get_details,
        ):
            self.submission.report.generate_submission_report_pdf()

        m_get_details.assert_called_once_with("a-remote-id")
