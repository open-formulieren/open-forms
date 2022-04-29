from dataclasses import dataclass
from typing import Iterator

from ..models import SubmissionStep
from .base import Node
from .constants import RenderModes


class FormNode(Node):
    """
    Render node for the submission form.
    """

    @property
    def is_visible(self):
        if self.mode == RenderModes.export:
            return False
        return True

    def get_children(self) -> Iterator:
        """
        Emit no child nodes.
        """
        return iter([])

    def render(self) -> str:
        """
        Emit the (public) name of the submission form.
        """
        form = self.renderer.form
        return form.name


@dataclass
class SubmissionStepNode(Node):
    step: SubmissionStep

    @property
    def is_visible(self) -> bool:
        # determine if the step as a whole is relevant or not. The stap may be not
        # applicable because of form logic.
        # logic_evaluated = getattr(self.step, "_form_logic_evaluated", False)
        # assert (
        #     logic_evaluated
        # ), "You should ensure that the form logic is evaluated before rendering steps!"
        return self.step.is_applicable

    def render(self) -> str:
        if self.mode == RenderModes.export:
            return ""
        form_definition = self.step.form_step.form_definition
        return form_definition.name

    def get_children(self) -> Iterator[Node]:
        if not self.is_visible:
            return

        return iter([])  # until we have the formio thing set up

        # # at this point, hand over to the formio specific implementation details
        # formio_configuration_node = FormioConfigurationNode(
        #     step=self.step, renderer=self.renderer
        # )
        # yield from formio_configuration_node
