from collections.abc import Iterator
from dataclasses import dataclass
from typing import cast

from json_logic.meta import JSONLogicExpressionTree, Operation
from json_logic.typing import JSON, Primitive

from .descriptions import _generate_description


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


def iter_tree(tree: JSONLogicExpressionTree) -> Iterator[Operation | Primitive]:
    if isinstance(tree, Primitive):
        yield tree

    elif isinstance(tree, list):
        for arg in tree:
            yield from iter_tree(arg)

    elif isinstance(tree, Operation):
        yield tree
        yield from iter_tree(tree.arguments)
