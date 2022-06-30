import webbrowser

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from ...models import Submission, SubmissionReport


class Command(BaseCommand):
    help = "Render the confirmation PDF for a given submission"

    def add_arguments(self, parser):
        parser.add_argument(
            "submission_id",
            type=int,
            help="Submission ID to generate the report for.",
        )
        parser.add_argument(
            "--open", action="store_true", help="Automatically open the resulting PDF"
        )

    def handle(self, **options):
        if not settings.DEBUG:
            raise CommandError("This command is only allowed in dev environments")

        submission = Submission.objects.get(pk=options["submission_id"])
        report, _ = SubmissionReport.objects.get_or_create(submission=submission)

        report.generate_submission_report_pdf()
        filepath = report.content.path
        self.stdout.write(f"Generated pdf: {filepath}")
        if options["open"]:
            webbrowser.open_new_tab(filepath)
