from django.core.management import BaseCommand

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
        else:
            self.stdout.write(
                "Registration completed or skipped (because it was already registered)."
            )
