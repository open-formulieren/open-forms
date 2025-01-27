from django.core.management import BaseCommand

from openforms.submissions.constants import PostSubmissionEvents, RegistrationStatuses
from openforms.submissions.models import Submission

from ...tasks import pre_registration, register_submission


class Command(BaseCommand):
    help = "Execute the registration machinery for a given submission"

    def add_arguments(self, parser):
        parser.add_argument(
            "submission_id", type=int, help="ID of submission to register"
        )
        parser.add_argument("--force", action="store_true")

    def handle(self, **options):
        if options["force"]:
            submission = Submission.objects.get(pk=options["submission_id"])
            submission.pre_registration_completed = False
            submission.registration_status = RegistrationStatuses.pending
            submission.registration_attempts = 0
            submission.registration_result = {}
            submission.save()

        self.stdout.write("Pre-registering submission...")
        try:
            pre_registration(
                options["submission_id"], PostSubmissionEvents.on_completion
            )
        except Exception as exc:
            self.stderr.write(f"Pre-registration failed with error: {exc}")
        else:
            self.stdout.write(
                "Pre-registration completed or skipped (because it was already pre-registered)."
            )

        self.stdout.write("Registering submission...")
        try:
            register_submission(
                options["submission_id"], PostSubmissionEvents.on_completion
            )
        except Exception as exc:
            self.stderr.write(f"Registration failed with error: {exc}")
        else:
            self.stdout.write(
                "Registration completed or skipped (because it was already registered)."
            )
