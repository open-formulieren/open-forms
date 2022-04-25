from django.conf import settings
from django.core.management import BaseCommand, CommandError

from tabulate import tabulate

from ...models import Submission
from ...rendering.renderer import Renderer, RenderModes

INDENT_SIZES = {
    "FormNode": 0,
    "FormStepNode": 1,
    "ComponentNode": 2,
}

INDENT = "    "


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

        prev_node_type, tabulate_data = None, []

        for node in renderer.render():
            indent_size = INDENT_SIZES.get(node.type, 0)
            lead = INDENT * indent_size

            if node.type == "ComponentNode":
                # extract label + value for tabulate data
                tabulate_data.append([node.label, node.display_value])
                prev_node_type = node.type
                continue
            else:
                # changed from component node to something else -> print the tabular data
                if prev_node_type == "ComponentNode":
                    self._print_tabulate_data(tabulate_data)
                    tabulate_data = []

            if node.type == "SubmissionStepNode":
                prev_node_type = node.type
                continue

            if lead:
                self.stdout.write(lead, ending="")
            self.stdout.write(node.render())
            prev_node_type = node.type

        self._print_tabulate_data(tabulate_data)

    def _print_tabulate_data(self, tabulate_data) -> None:
        if not tabulate_data:
            return

        table = tabulate(tabulate_data)
        _lead = INDENT * INDENT_SIZES["ComponentNode"]
        for line in table.splitlines():
            self.stdout.write(f"{_lead}{line}")
