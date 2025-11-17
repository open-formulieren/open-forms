from collections.abc import Iterator
from dataclasses import dataclass
from typing import TypedDict

from json_logic.meta import JSONLogicExpressionTree, Operation
from json_logic.typing import JSON, Primitive

from .descriptions import _generate_description

REDUCE_VAR_NAMES: list[str] = ["current", "accumulator"]


class LogicContext(TypedDict):
    in_reduce: bool


@dataclass(frozen=True)
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
        for node, context in iter_tree(self.tree, LogicContext(in_reduce=False)):
            if isinstance(node, Primitive):
                continue
            if node.operator != "var":
                continue
            if not isinstance(node.arguments[0], str):
                continue

            key = node.arguments[0]
            if key in REDUCE_VAR_NAMES and context["in_reduce"]:
                continue

            inputs.append(InputVar(key=key))

        return inputs


def iter_tree(
    tree: JSONLogicExpressionTree, context: LogicContext
) -> Iterator[tuple[Operation | Primitive, LogicContext]]:
    if isinstance(tree, Primitive):
        yield tree, context

    elif isinstance(tree, list):
        for arg in tree:
            yield from iter_tree(arg, context)

    elif isinstance(tree, Operation):
        yield tree, context
        operation_context = LogicContext(
            in_reduce=tree.operator.lower() == "reduce" or context["in_reduce"]
        )
        yield from iter_tree(tree.arguments, operation_context)
