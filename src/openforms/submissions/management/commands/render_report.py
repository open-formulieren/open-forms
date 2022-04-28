from django.conf import settings
from django.core.management import BaseCommand, CommandError

from tabulate import tabulate

from openforms.formio.rendering import ComponentNode

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
            nargs="+",
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
        parser.add_argument(
            "--as-html",
            action="store_true",
            help="Enable HTML output instead of plain text.",
        )
        parser.add_argument(
            "--render-mode",
            choices=[c[0] for c in RenderModes.choices],
            default=RenderModes.cli,
            help=f"Simulate a particular render mode. Defaults to {RenderModes.cli}",
        )

    def handle(self, **options):
        if not settings.DEBUG:
            raise CommandError("This command is only allowed in dev environments")

        self.limit_value_keys = options["limit_value_key"]
        for submission_id in options["submission_id"]:
            self.render_submission(
                submission_id,
                render_mode=options["render_mode"],
                as_html=options["as_html"],
            )

    def render_submission(self, submission_id: int, render_mode: str, as_html=False):
        submission = Submission.objects.get(pk=submission_id)

        renderer = Renderer(
            submission=submission,
            mode=render_mode,
            as_html=as_html,
            limit_value_keys=self.limit_value_keys or None,
        )

        self.stdout.write("")
        self.stdout.write(f"Submission {submission.id} - ", ending="")

        prev_node_type, tabulate_data = None, []

        for node in renderer.render():
            indent_size = INDENT_SIZES.get(node.type, 0)
            lead = INDENT * indent_size

            if isinstance(node, ComponentNode):
                # extract label + value for tabulate data
                tabulate_data.append([node.label, node.display_value])
                prev_node_type = "ComponentNode"
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
