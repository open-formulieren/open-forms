from django.core.management import BaseCommand

from openforms.submissions.models import Submission

from ...service import extract_submission_reference
from ...tasks import register_submission


class Command(BaseCommand):
    help = "Execute the registration machinery for a given submission"

    def add_arguments(self, parser):
        parser.add_argument(
            "submission_id", type=int, help="ID of submission to register"
        )

    def handle(self, **options):
        self.stdout.write("Registering submission...")
        try:
            register_submission(options["submission_id"])
        except Exception as exc:
            self.stderr.write(f"Registration failed with error: {exc}")
            return

        self.stdout.write(
            "Registration completed or skipped (because it was already registered)."
        )

        submission = Submission.objects.get(pk=options["submission_id"])
        reference = extract_submission_reference(submission)
        self.stdout.write(f"Submission reference: {reference}")
