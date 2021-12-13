from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from privates.test import temp_private_root

from ..models import SubmissionReport
from ..tasks.pdf import generate_submission_report
from .factories import SubmissionFactory


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
