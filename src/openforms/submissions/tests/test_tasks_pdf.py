import logging

from django.test import TestCase
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from privates.test import temp_private_root
from testfixtures import LogCapture

from ..models import SubmissionReport
from ..tasks.pdf import generate_submission_report
from .factories import SubmissionFactory, SubmissionReportFactory


@temp_private_root()
class SubmissionReportGenerationTests(TestCase):
    def test_submission_report_metadata(self):
        submission = SubmissionFactory.create(completed=True, form__name="Test Form")

        generate_submission_report.request.id = "some-id"
        generate_submission_report.run(submission.id)

        report = SubmissionReport.objects.get()
        self.assertEqual(
            _("%(title)s: Submission report") % {"title": "Test Form"}, report.title
        )
        self.assertEqual(submission, report.submission)
        self.assertTrue(report.content.name.endswith("Test_Form.pdf"))
        self.assertEqual("some-id", report.task_id)

    def test_multiple_value_report_rendering_issue_990(self):
        # regression test for Github #990
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "email",
                    "label": "email",
                    "type": "email",
                    "multiple": True,
                }
            ],
            # a multiple email field with no value entered sends a [None]
            {"email": [None]},
            completed=True,
            with_report=False,
        )

        generate_submission_report.request.id = "some-id"
        generate_submission_report.run(submission.id)

        report = SubmissionReport.objects.get()
        self.assertEqual(submission, report.submission)

    def test_pdf_renders_without_errors(self):
        """
        Assert that no error logs are emitted while rendering the PDF.

        This turned up as part of #949 - the PDF restyling which now uses "external"
        stylesheets and fonts for the layout. Using STATIC_URL=/static/ led to relative
        URLs without base URI and thus making it impossible to fetch the actual
        resources. This manifested in WeasyPrint as log records with log level ERROR.
        """
        report = SubmissionReportFactory.create(content="", submission__completed=True)

        with LogCapture(level=logging.ERROR) as capture:
            report.generate_submission_report_pdf()

        capture.check()

    def test_hidden_output_not_included(self):
        """
        Assert that hidden components are not included in the report.

        #1451 requires that components hidden (statically or) dynamically by logic
        are not included. The report functionality is also extended to add more
        structure, and step titles/headers may not be included if there's nothing
        visible in the step.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "input1",
                    "label": "Input 1",
                    "type": "textfield",
                    "hidden": True,
                }
            ],
            submitted_data={},
            completed=True,
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()
        step_title = submission.submissionstep_set.get().form_step.form_definition.name

        # hidden component itself may not be visible
        self.assertNotIn("Input 1", html)
        # step has no visible children -> also not visible
        self.assertNotIn(step_title, html)

    def test_visible_output_included(self):
        """
        Assert that hidden components are not included in the report.

        #1451 requires that components hidden (statically or) dynamically by logic
        are not included. The report functionality is also extended to add more
        structure, and step titles/headers may not be included if there's nothing
        visible in the step.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "input1",
                    "label": "Input 1",
                    "type": "textfield",
                    "hidden": True,
                },
                {
                    "key": "input2",
                    "label": "Input 2",
                    "type": "textfield",
                    "hidden": False,
                },
                {
                    "type": "fieldset",
                    "label": "Group of fields",
                    "key": "group",
                    "components": [
                        {
                            "type": "currency",
                            "label": "Money money money",
                            "key": "money",
                            "hidden": False,
                        }
                    ],
                },
                {
                    "type": "content",
                    "html": "<p>Some markup</p>",
                    "key": "content",
                },
            ],
            submitted_data={"input1": None, "input2": "Second input", "money": 1234.56},
            completed=True,
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()
        step_title = submission.submissionstep_set.get().form_step.form_definition.name

        self.assertIn(step_title, html)
        self.assertNotIn("Input 1", html)
        self.assertIn("Input 2", html)
        self.assertIn("Second input", html)
        self.assertIn("Group of fields", html)
        self.assertIn("Money money money", html)
        self.assertIn("1.234,56", html)
        self.assertInHTML("<p>Some markup</p>", html)


@temp_private_root()
class SubmissionReportCoSignTests(TestCase):
    def test_cosign_data_included(self):
        report = SubmissionReportFactory.create(
            content="",
            submission__completed=True,
            submission__co_sign_data={
                "plugin": "digid",
                "identifier": "123456782",
                "fields": {
                    "voornaam": "Tina",
                    "geslachtsnaam": "Shikari",
                },
                "representation": "T. Shikari",
            },
        )

        rendered: str = report.generate_submission_report_pdf()

        report.refresh_from_db()
        self.assertTrue(report.content.name.endswith(".pdf"))
        expected = format_html(
            """
            <div class="submission-step-row">
                <div class="submission-step-row__label">{key}</div>
                <div class="submission-step-row__value">T. Shikari</div>
            </div>
            """,
            key=_("Co-signed by"),
        )
        self.assertInHTML(expected, rendered, count=1)
