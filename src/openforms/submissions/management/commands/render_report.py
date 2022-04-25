from django.conf import settings
from django.core.management import BaseCommand, CommandError

from ...models import Submission
from ...rendering.renderer import Renderer, RenderModes

INDENT_SIZES = {
    "FormNode": 0,
    "FormStepNode": 1,
}


class Command(BaseCommand):
    help = (
        "Display the submission data in the terminal. This is a proof of concept of a "
        "generic rendering API capable of outputting to different modes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "submission_id",
            type=int,
            help="Submission ID to display data from.",
        )
        parser.add_argument(
            "-l",
            "--limit-value-key",
            nargs="+",
            help=(
                "If provided, limits the output data keys to the specified set. Can be "
                "specified multiple times."
            ),
        )

    def handle(self, **options):
        if not settings.DEBUG:
            raise CommandError("This command is only allowed in dev environments")

        submission = Submission.objects.get(pk=options["submission_id"])
        limit_value_keys = options["limit_value_key"]

        renderer = Renderer(
            submission=submission,
            mode=RenderModes.cli,
            as_html=False,
            limit_value_keys=limit_value_keys or None,
        )

        self.stdout.write("")
        for node in renderer.render():
            if node.type == "SubmissionStepNode":
                continue

            indent_size = INDENT_SIZES[node.type]
            lead = "    " * indent_size
            if lead:
                self.stdout.write(lead, ending="")

            self.stdout.write(node.render())
