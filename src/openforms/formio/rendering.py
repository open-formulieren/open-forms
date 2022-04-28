from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Iterator, Optional, Union

from django.utils.safestring import SafeString, mark_safe

from openforms.emails.utils import strip_tags_plus
from openforms.submissions.models import SubmissionStep
from openforms.submissions.rendering.base import Node
from openforms.submissions.rendering.constants import RenderModes

from .formatters.service import format_value
from .typing import Component
from .utils import iter_components

if TYPE_CHECKING:
    from openforms.submissions.rendering.renderer import Renderer


COMPONENT_TYPE_NODES = {}


def register(component_type: str):
    def decorator(cls):
        COMPONENT_TYPE_NODES[component_type] = cls
        return cls

    return decorator


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
    depth: int = 0

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
        node_cls = COMPONENT_TYPE_NODES.get(component["type"], ComponentNode)
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
        """
        if self.component.get("hidden") is True:
            return False

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

    def get_children(self) -> Iterator["ComponentNode"]:
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
        Yield depth-first children.
        """
        if not self.is_visible:
            return

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
        if self.renderer.mode == RenderModes.export:
            return self.component.get("key") or "KEY_MISSING"
        return self.component.get("label") or self.component.get("key", "")

    @property
    def display_value(self) -> str:
        # in export mode, expose the raw datatype
        if self.renderer.mode == RenderModes.export:
            return self.value
        return format_value(self.component, self.value, as_html=self.renderer.as_html)

    def render(self) -> str:
        return f"{self.label}\t\t\t{self.display_value}"


class ContainerMixin:
    @property
    def is_visible(self) -> bool:
        # fieldset does not support the showInFoo properties, so we don't use the super
        # class.
        if self.component.get("hidden") is True:
            return False

        render_configuration = VISIBILITY_ATTRIBUTE_MAP[self.renderer.mode]
        if render_configuration.attribute is not None:
            assert render_configuration.attribute not in self.component, (
                f"Component type {self.component['type']} unexpectedly seems to support "
                f"the {render_configuration.attribute} property!"
            )

        any_children_visible = any((child.is_visible for child in self.get_children()))
        if not any_children_visible:
            return False

        return True


@register("fieldset")
class FieldSetNode(ContainerMixin, ComponentNode):
    layout_modifier = "fieldset"


@register("columns")
class ColumnsNode(ContainerMixin, ComponentNode):
    layout_modifier = "columns"


@register("content")
class WYSIWYGNode(ComponentNode):
    @property
    def is_visible(self) -> bool:
        visible_from_config = super().is_visible
        if not visible_from_config:
            return False
        return self.renderer.mode in (
            RenderModes.cli,
            RenderModes.pdf,
        )

    @property
    def value(self) -> Union[str, SafeString]:
        content = self.component["html"]
        if self.renderer.as_html:
            return mark_safe(content)

        return strip_tags_plus(content)


@dataclass
class FormioConfigurationNode(Node):
    # TODO: use dynamic SubmissionStep configuration instead which has the logic evaluated!
    step: SubmissionStep

    def render(self) -> str:
        return ""

    def __iter__(self) -> Iterator[ComponentNode]:
        for component in self.step.form_step.iter_components(
            recursive=False, _mark_root=True
        ):
            nested_node = ComponentNode.build_node(
                step=self.step, component=component, renderer=self.renderer
            )
            yield from nested_node
