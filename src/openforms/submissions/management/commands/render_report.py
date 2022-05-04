"""
Management command to simulate the submission renderer outputting to a particular mode.

On top of that, it is also a realistic example of using the high-level Python API for
the renderer to output reports.
"""
import inspect
from typing import List, Type, Union

from django.core.management import BaseCommand

from tabulate import tabulate

from openforms.formio.rendering.nodes import ComponentNode

from ...models import Submission
from ...rendering.nodes import Node, SubmissionStepNode
from ...rendering.renderer import Renderer, RenderModes

INDENT_SIZES = {
    SubmissionStepNode: 1,
    ComponentNode: 2,
}

INDENT = "    "


def get_indent_level(node_cls: Union[Node, Type[Node]]) -> str:
    """
    Extract the indentation level from the node class configuration.
    """
    if not inspect.isclass(node_cls):
        node_cls = node_cls.__class__
    for cls in node_cls.__mro__:
        if cls in INDENT_SIZES:
            indent_size = INDENT_SIZES[cls]
            break
    else:
        indent_size = 0
    lead = INDENT * indent_size
    return lead


class Command(BaseCommand):
    help = (
        "Display the submission data in the terminal with your desired render mode. "
        "You may want to specify the LOG_LEVEL=WARNING envvar to surpress log output."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "submission_id",
            type=int,
            nargs="+",
            help="Submission ID(s) to display the data from.",
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
            help=f"Simulate a particular render mode. Defaults to {RenderModes.cli}.",
        )

    def handle(self, **options):
        submissions = Submission.objects.filter(
            id__in=options["submission_id"]
        ).order_by("id")
        for submission in submissions:
            self.render_submission(
                submission,
                render_mode=options["render_mode"],
                as_html=options["as_html"],
            )

    def render_submission(self, submission: int, render_mode: str, as_html=False):
        renderer = Renderer(submission=submission, mode=render_mode, as_html=as_html)

        self.stdout.write("")
        self.stdout.write(f"Submission {submission.id} - ", ending="")

        prev_node_type, tabulate_data = None, []

        for node in renderer:
            lead = get_indent_level(node)
            if isinstance(node, ComponentNode):
                # do not emit empty lines
                if not node.label and not node.display_value:
                    continue
                # extract label + value for tabulate data
                tabulate_data.append([node.label, node.display_value])
                prev_node_type = ComponentNode
                continue
            else:
                # changed from component node to something else -> print the tabular data
                if prev_node_type == ComponentNode:
                    self._print_tabulate_data(tabulate_data)
                    tabulate_data = []

            if lead:
                self.stdout.write(lead, ending="")
            self.stdout.write(node.render())
            prev_node_type = type(node)

        self._print_tabulate_data(tabulate_data)

    def _print_tabulate_data(self, tabulate_data: List[List[str]]) -> None:
        if not tabulate_data:
            return
        table = tabulate(tabulate_data)
        lead = get_indent_level(ComponentNode)
        for line in table.splitlines():
            self.stdout.write(f"{lead}{line}")
