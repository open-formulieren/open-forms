from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.test import override_settings

from ...models import Submission, SubmissionReport

WEASYPRINT_LOGGING = {
    **settings.LOGGING,
    "loggers": {
        "weasyprint": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        }
    },
}


class Command(BaseCommand):
    help = "Render the confirmation PDF for a given submission"

    def add_arguments(self, parser):
        parser.add_argument(
            "submission_id",
            type=int,
            help="Submission ID to generate the report for.",
        )

    def handle(self, **options):
        if not settings.DEBUG:
            raise CommandError("This command is only allowed in dev environments")

        submission = Submission.objects.get(pk=options["submission_id"])
        report, _ = SubmissionReport.objects.get_or_create(submission=submission)

        with override_settings(LOGGING=WEASYPRINT_LOGGING):
            report.generate_submission_report_pdf()
