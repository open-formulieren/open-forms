from collections.abc import Iterator
from dataclasses import dataclass

import structlog

from openforms.formio.rendering.nodes import FormioNode

from ..models import SubmissionStep
from .base import Node
from .constants import RenderModes

logger = structlog.stdlib.get_logger(__name__)


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
    """
    Render node for a single submission step.

    This node is only considered 'visible' if the step is applicable (determined by
    form logic). If the step is not visible, no child nodes are emitted.

    Rendering this node outputs the name of the step within the form.
    """

    step: SubmissionStep

    @property
    def is_visible(self) -> bool:
        if self.mode == RenderModes.export:
            return True
        # determine if the step as a whole is relevant or not. The stap may be not
        # applicable because of form logic.
        logic_evaluated = getattr(self.step, "_form_logic_evaluated", False)
        if not logic_evaluated:
            # logic should really be evaluated before rendering steps!
            logger.warning(
                "submissions.rendering.logic_not_evaluated",
                submission_uuid=str(self.step.submission.uuid),
                renderer=self.renderer,
                step_uuid=str(self.step.uuid),
            )
        return self.step.is_applicable

    def render(self) -> str:
        if self.mode == RenderModes.export:
            return ""
        form_definition = self.step.form_step.form_definition
        return form_definition.name

    def get_children(self) -> Iterator[Node]:
        if not self.is_visible:
            return

        yield from FormioNode(step=self.step, renderer=self.renderer)
