import time

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.test import RequestFactory

from rest_framework.request import Request

from ...constants import ProcessingStatuses
from ...models import Submission
from ...status import SubmissionProcessingStatus
from ...tasks import on_completion


class Command(BaseCommand):
    # This management command is purely intended to test the celery submission completion
    # orchestration!
    # Note that you should have a worker running listening to the broker.
    help = "Generate a submission and test the completion process flow"

    def add_arguments(self, parser):
        parser.add_argument(
            "--submission-id",
            type=int,
            help="Re-use an existing submission to test.",
        )
        parser.add_argument(
            "--with-incomplete-appointment",
            action="store_true",
            help="Generate a submission for an incompletely filled appointment form",
        )
        parser.add_argument(
            "--with-payment",
            action="store_true",
            help="Generate a submission for a form requiring payment (TODO: implement)",
        )

    def handle(self, **options):
        if not settings.DEBUG:
            raise CommandError("This command is only allowed in dev environments")

        # local imports since the test tooling is not part of the base dependencies!
        from ...tests.factories import SubmissionFactory

        self.stdout.write("Generating submission from factory...")

        factory_kwargs = {}
        if options["with_incomplete_appointment"]:
            factory_kwargs["components_list"] = [
                {
                    "key": "productID",
                    "appointmentsShowProducts": True,
                }
            ]
            factory_kwargs["submitted_data"] = {
                "productID": "123",
            }

        if submission_id := options["submission_id"]:
            submission = Submission.objects.get(id=submission_id)
        else:
            submission = SubmissionFactory.from_components(
                completed=True,
                **factory_kwargs,
            )

        self.stdout.write(f"Submission: {submission.id}")
        self.stdout.write("Entering on_completion flow...")
        on_completion(submission.id)

        submission.refresh_from_db()
        request = RequestFactory().get("/irrelevant")
        processing_status = SubmissionProcessingStatus(
            request=Request(request), submission=submission
        )

        while processing_status.status == ProcessingStatuses.in_progress:
            self.stdout.write("Still processing...")
            time.sleep(1)

        self.stdout.write(f"Processing complete, result: {processing_status.result}")
        processing_status.forget_results()
