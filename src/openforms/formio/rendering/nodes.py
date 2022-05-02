from dataclasses import dataclass
from typing import Any, Iterator, Optional, Union

from openforms.submissions.models import SubmissionStep
from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.rendering.base import Node

from ..formatters.service import format_value
from ..typing import Component
from ..utils import iter_components


@dataclass
class RenderConfiguration:
    """
    Component-level property configuration to control output.

    Whether a component should be emitted or not is/can be configured on the component
    in the form designer. In the event that this key is missing from the component (
    because it is not supported or is a form definition from before this feature
    landed), then fall back using the ``default``.
    """

    key: Optional[str]
    default: bool


@dataclass
class ComponentNode(Node):
    component: Component
    step: SubmissionStep
    depth: int = 0
    is_layout = False

    @staticmethod
    def build_node(
        step: SubmissionStep,
        component: Component,
        renderer: "Renderer",
        depth: int = 0,
    ) -> "ComponentNode":
        """
        Instantiate the most specific node type for a given component type.
        """
        from .registry import register

        node_cls = register[component["type"]]
        nested_node = node_cls(
            step=step, component=component, renderer=renderer, depth=depth
        )
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

        These exceptions are handled in more specific subclasses to avoid massive if-else
        branches again, see :mod:`openforms.formio.rendering.default`.
        """
        from .conf import RENDER_CONFIGURATION  # circular import

        # everything is emitted in export mode to get consistent columns
        if self.mode == RenderModes.export:
            return True

        # explicitly hidden components never show up. Note that this property can be set
        # by form logic!
        if self.component.get("hidden") is True:
            return False

        render_configuration = RENDER_CONFIGURATION[self.mode]
        # it's possible the end-user cannot explicitly configure the visibility, in
        # which case the system default is used.
        if render_configuration.key is None:
            return render_configuration.default

        # if there is a property key, try to read it but fall back to the system default
        # if it's absent.
        should_render = self.component.get(
            render_configuration.key, render_configuration.default
        )
        return should_render

    @property
    def value(self) -> Any:
        """
        Obtain the value from the submission for this component.

        Note that this returns an unformatted value. There also has not been done
        any Formio type -> Python type casting, so a datetime will be an ISO-8601
        datestring for example.

        TODO: build and use the type conversion for Formio components.
        """
        key = self.component["key"]
        value = self.step.data.get(key)
        return value

    def get_children(self) -> Iterator["ComponentNode"]:
        """
        Yield the child components if this component is a container type.
        """
        for component in iter_components(
            configuration=self.component, recursive=False, _is_root=False
        ):
            yield ComponentNode.build_node(
                step=self.step,
                component=component,
                renderer=self.renderer,
                depth=self.depth + 1,
            )

    def __iter__(self) -> Iterator["ComponentNode"]:
        """
        Yield depth-first children, including itself.
        """
        if not self.is_visible:
            return

        # in export mode, only emit if there's a 'key' property
        if self.mode != RenderModes.export or "key" in self.component:
            yield self

        for child in self.get_children():
            if not child.is_visible:
                continue
            yield from child

    @property
    def layout_modifier(self) -> str:
        """
        For HTML based rendering, potentially emit a layout modifier.
        """
        return "root" if self.component.get("_is_root", False) else ""

    @property
    def label(self) -> str:
        """
        Obtain the (human-readable) label for the Formio component.
        """
        if self.mode == RenderModes.export:
            return self.component.get("key") or "KEY_MISSING"
        return self.component.get("label") or self.component.get("key", "")

    @property
    def display_value(self) -> Union[str, Any]:
        """
        Format the value according to the render mode and/or output content type.

        This applies the registry of Formio formatters to the value based on the
        component type, using :func:`openforms.formio.formatter.service.format_value`.
        """
        # in export mode, expose the raw datatype
        if self.mode == RenderModes.export:
            return self.value
        return format_value(self.component, self.value, as_html=self.renderer.as_html)

    def render(self) -> str:
        """
        Output a simple key-value pair of label and value.
        """
        indent = "    " * self.depth if not self.as_html else ""
        return f"{indent}{self.label}: {self.display_value}"
