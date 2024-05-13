from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator, cast

from glom import glom
from json_logic.meta import JSONLogicExpressionTree, Operation
from json_logic.typing import JSON, Primitive

from openforms.formio.typing import Component

from .descriptions import _generate_description

if TYPE_CHECKING:
    from openforms.forms.models import FormStep

__all__ = ["ComponentMeta"]

ComponentsMap = dict[str, "ComponentMeta"]


@dataclass
class ComponentMeta:
    form_step: "FormStep"
    component: "Component"


@dataclass(slots=True)
class InputComponentVar:
    key: str
    value: JSON
    step_name: str
    label: str


@dataclass
class InputVar:
    key: str


@dataclass
class ExpressionIntrospection:
    expression: JSON
    tree: JSONLogicExpressionTree

    @property
    def description(self) -> str:
        return _generate_description(self.tree, root=True)

    def get_input_keys(self) -> list[InputVar]:
        inputs = []
        for node in iter_tree(self.tree):
            if isinstance(node, Primitive):
                continue
            if node.operator != "var":
                continue
            if not isinstance(node.arguments[0], str):
                continue

            key = cast(str, node.arguments[0])
            inputs.append(InputVar(key=key))

        return inputs

    def get_input_components(
        self,
        components_map: ComponentsMap,
        input_data: dict[str, JSON],
    ) -> list[InputComponentVar]:
        inputs = []

        for node in iter_tree(self.tree):
            if isinstance(node, Primitive):
                continue
            if node.operator != "var":
                continue

            # TODO: this *may* be nested var.var expressions
            key = cast(str, node.arguments[0])
            step_name = label = ""
            if component_meta := components_map.get(key):
                step_name = component_meta.form_step.form_definition.name
                label = component_meta.component.get("label", "")
            inputs.append(
                InputComponentVar(
                    key=key,
                    value=glom(input_data, key, default=""),
                    step_name=step_name,
                    # TODO: take translations into account?
                    label=label,
                )
            )

        return inputs


def iter_tree(tree: JSONLogicExpressionTree) -> Iterator[Operation | Primitive]:
    if isinstance(tree, Primitive):
        yield tree

    elif isinstance(tree, list):
        for arg in tree:
            yield from iter_tree(arg)

    elif isinstance(tree, Operation):
        yield tree
        yield from iter_tree(tree.arguments)
