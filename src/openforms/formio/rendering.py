from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterator, Optional

from openforms.submissions.models import SubmissionStep
from openforms.submissions.rendering.base import Node
from openforms.submissions.rendering.constants import RenderModes

from .formatters.service import format_value
from .typing import Component
from .utils import iter_components

if TYPE_CHECKING:
    from openforms.submissions.rendering.renderer import Renderer


COMPONENT_TYPE_NODES = {}


@dataclass
class RenderConfiguration:
    attribute: Optional[str]
    default: bool


VISIBILITY_ATTRIBUTE_MAP = {
    RenderModes.cli: RenderConfiguration(attribute=None, default=True),
    RenderModes.pdf: RenderConfiguration(attribute="showInPDF", default=True),
    RenderModes.confirmation_email: RenderConfiguration(
        attribute="showInEmail", default=False
    ),
    RenderModes.export: RenderConfiguration(attribute=None, default=True),
}
"""
Map render modes to the component configuration key to check with their defaults.
"""


@dataclass
class ComponentNode(Node):
    component: Component
    step: SubmissionStep

    @staticmethod
    def build_node(
        step: SubmissionStep, component: Component, renderer: "Renderer"
    ) -> "ComponentNode":
        """
        Instantiate the most specific node type for a given component type.
        """
        node_cls = COMPONENT_TYPE_NODES.get(component["type"], ComponentNode)
        nested_node = node_cls(step=step, component=component, renderer=renderer)
        return nested_node

    @property
    def is_visible(self) -> bool:
        """
        Implement the logic to determine if a component is visible.

        See https://github.com/open-formulieren/open-forms/issues/1451#issuecomment-1077506877
        for a diagram of the logic powering this.

        Summarized, a component is visible for a given render mode if the component-level
        configuration says so (while falling back to some defaults for older configurations).

        The exceptions to this are:

        - fieldsets are visible if:
          - any of the children is visible (no render_mode dependency)
          - not `hidden` (no render_mode dependency)
          - (not `hideHeader`) -> render children, but not the label

        - fieldsets:
          - never render the label

        - wysiwyg:
          - in PDF if visible
        """
        render_configuration = VISIBILITY_ATTRIBUTE_MAP[self.renderer.mode]
        if render_configuration.attribute is None:
            return render_configuration.default
        should_render = self.component.get(
            render_configuration.attribute, render_configuration.default
        )
        return should_render

    @property
    def value(self) -> Any:
        key = self.component["key"]
        value = self.step.data.get(key)
        return value

    def __iter__(self) -> Iterator["ComponentNode"]:
        """
        Yield depth-first children.
        """
        if not self.is_visible:
            return

        yield self

        for component in iter_components(
            configuration=self.component, recursive=False, _is_root=False
        ):
            nested_node = ComponentNode.build_node(
                step=self.step, component=component, renderer=self.renderer
            )
            if not nested_node.is_visible:
                continue
            yield nested_node
            yield from nested_node

    @property
    def label(self) -> str:
        return self.component.get("label") or self.component.get("key", "")

    @property
    def display_value(self) -> str:
        return format_value(self.component, self.value, as_html=self.renderer.as_html)

    def render(self) -> str:
        return f"{self.label}\t\t\t{self.display_value}"


@dataclass
class FormioConfigurationNode(Node):
    # TODO: use dynamic SubmissionStep configuration instead which has the logic evaluated!
    step: SubmissionStep

    def render(self) -> str:
        return ""

    @property
    def is_visible(self) -> bool:
        # TODO: move to SubmissionStepNode
        # determine if the step as a whole is relevant or not. The stap may be not
        # applicable because of form logic.
        logic_evaluated = getattr(self.step, "_form_logic_evaluated", False)
        assert (
            logic_evaluated
        ), "You should ensure that the form logic is evaluated before rendering steps!"
        return self.step.is_applicable

    def __iter__(self) -> Iterator[ComponentNode]:
        if not self.is_visible:
            return

        for component in self.step.form_step.iter_components(
            recursive=False, _mark_root=True
        ):
            nested_node = ComponentNode.build_node(
                step=self.step, component=component, renderer=self.renderer
            )
            yield from nested_node
