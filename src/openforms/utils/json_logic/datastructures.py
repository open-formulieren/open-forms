from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator, cast

from json_logic.meta import JSONLogicExpressionTree, Operation
from json_logic.typing import JSON, Primitive

from openforms.formio.typing import Component
from openforms.typing import DataMapping

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
class InputVar:
    key: str
    value: JSON
    step_name: str
    label: str


@dataclass
class ExpressionIntrospection:
    expression: JSON
    tree: JSONLogicExpressionTree

    @property
    def description(self) -> str:
        return _generate_description(self.tree, root=True)

    def get_input_components(
        self,
        components_map: ComponentsMap,
        input_data: dict[str, JSON],
        context: DataMapping,
    ) -> list[InputVar]:
        inputs = []

        for node in iter_tree(self.tree):
            if isinstance(node, Primitive):
                continue
            if node.operator != "var":
                continue

            # TODO: this *may* be nested var.var expressions
            key = cast(str, node.arguments[0])
            if key not in components_map:
                inputs.append(
                    InputVar(key=key, value=context[key], step_name="", label="")
                )
                continue
            component_meta = components_map[key]
            inputs.append(
                InputVar(
                    key=key,
                    value=input_data.get(key, ""),
                    step_name=component_meta.form_step.form_definition.name,
                    # TODO: take translations into account?
                    label=component_meta.component.get("label", ""),
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
