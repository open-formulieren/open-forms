from dataclasses import dataclass
from typing import Any, Iterator

from openforms.submissions.models import SubmissionStep
from openforms.submissions.rendering.base import Node

from .formatters.service import format_value
from .typing import Component


@dataclass
class ComponentNode(Node):
    component: Component
    value: Any

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

    def __iter__(self) -> Iterator[ComponentNode]:
        for component in self.step.form_step.iter_components(
            recursive=True, _mark_root=True
        ):
            key = component["key"]
            value = self.step.data.get(key)
            yield ComponentNode(
                component=component, value=value, renderer=self.renderer
            )
