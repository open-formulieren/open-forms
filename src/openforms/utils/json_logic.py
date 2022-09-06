"""
Utilities to parse/process jsonLogic expressions.
"""
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Union

from json_logic import jsonLogic

if TYPE_CHECKING:
    from openforms.formio.typing import Component
    from openforms.forms.models import FormStep

__all__ = ["JsonLogicTest"]

JSONLogicValue = Union[str, int, "JsonLogicTest"]
JsonLogicExpression = Dict[str, Any]
JsonLogicNode = Union["JsonLogicLeaf", "JsonLogicOperation"]


@dataclass
class JsonLogicTest:
    operator: str
    values: List[JSONLogicValue] = field(default_factory=list)

    @classmethod
    def from_expression(cls, expression: dict):
        try:
            jsonLogic(expression)
        except ValueError as exc:
            raise ValueError("Invalid jsonLogic expression given") from exc

        operator = list(expression.keys())[0]
        values = expression[operator]

        # convert unary syntactic sugar to normalized format
        if not isinstance(values, (list, tuple)):
            values = [values]

        normalized = [normalize_value(value) for value in values]
        return cls(
            operator=operator,
            values=normalized,
        )


def normalize_value(value: Union[dict, list, tuple, int, str]) -> JSONLogicValue:
    if not isinstance(value, (dict, list)):
        return value

    # not sure how correct this is :grimacing:
    if isinstance(value, (list, tuple)):
        return [normalize_value(val) for val in value]

    if isinstance(value, dict):
        return JsonLogicTest.from_expression(value)

    raise NotImplementedError(f"Unknown value type: {type(value)}")


@dataclass
class ComponentMeta:
    form_step: "FormStep"
    component: "Component"


@dataclass
class IntrospectionResult:

    expression: dict
    rule_tree: "JsonLogicOperation"

    def as_string(self) -> str:
        return stringify_json_tree(self.rule_tree)

    def get_input_components(self) -> List[JsonLogicExpression]:
        return get_leaves(self.rule_tree)


@dataclass
class JsonLogicLeaf:
    key: str
    actual_value: str
    step_name: str
    label: str


@dataclass
class JsonLogicOperation:
    operator: str
    children: List[JsonLogicNode]
    value: str


def introspect_json_logic(
    expression: JsonLogicExpression,
    components_map: Dict[str, ComponentMeta],
    input_data: JsonLogicExpression,
) -> IntrospectionResult:
    logic_expression = JsonLogicTest.from_expression(expression)
    rule_tree = convert_json_logic_in_json_tree(
        logic_expression, components_map, input_data
    )
    return IntrospectionResult(expression=expression, rule_tree=rule_tree)


def find_json_logic_test_value(value: JsonLogicTest) -> str:
    """returns the value inside a JsonLogicTest"""
    if isinstance(value, JsonLogicTest) and value.operator in ["date", "var"]:
        return find_json_logic_test_value(value.values[0])
    else:
        return value


def convert_json_logic_in_json_tree(
    logics, component_map, resulting_data
) -> JsonLogicOperation:
    """returns a tree of JsonLogicNode's type nodes

    This function transforms a logic_rule into a tree with information related to the
    components involved in the rule such as its `value`, `label`, `step name`...

    :param logics:  :class:`JsonLogicTest` the logic rule
    :param component_map: formLogic and component mapped to the related key
    :param resulting_data: actual data from the submission form


    :rtype: JsonLogicOperation
    :return: rule with additional information related to the involved component


    """
    # array of rules
    if not isinstance(logics, JsonLogicTest):
        return [
            convert_json_logic_in_json_tree(logic, component_map, resulting_data)
            for logic in logics
        ]
    json_logic_operation = JsonLogicOperation(
        operator=logics.operator, children=[], value=""
    )
    for index, value in enumerate(logics.values):

        # There is an operation
        if isinstance(value, JsonLogicTest):
            if value.operator in ["var", "date"]:
                key = find_json_logic_test_value(logics.values[index])
                # leaf not related to component --> just a value compared
                if not component_map.get(key):
                    json_logic_operation.value = key

                # Leaf is a field
                else:
                    json_logic_value = JsonLogicLeaf(
                        key=key,
                        actual_value=resulting_data.get(key, ""),
                        step_name=component_map[key].form_step.form_definition.name,
                        label=component_map[key].component.get("label", ""),
                    )
                    json_logic_operation.children.append(json_logic_value)
            elif value.operator == "rdelta":
                json_logic_operation.value = value.values

            # No relevant information with this operator
            elif value.operator == "today":
                pass
            else:
                json_logic_operation.children.append(
                    convert_json_logic_in_json_tree(
                        value,
                        component_map,
                        resulting_data,
                    )
                )

        # No operation, it's a basic value
        else:
            json_logic_operation.value = value

    # return logic_dict
    return json_logic_operation


def stringify_json_tree(node: JsonLogicNode) -> str:
    """transform the json_tree in a string of rules"""

    # Unary operation
    if not node.children:
        return f"{node.operator} {node.value}"

    output = ""
    children_number = len(node.children)
    for index, child in enumerate(node.children):
        last_child = index == children_number - 1
        if isinstance(child, JsonLogicLeaf):
            output += child.key
        else:
            output += f"({stringify_json_tree(child)})"
        if node.value != "":
            output += f" {node.operator} {node.value}"
        else:
            output += f" {node.operator} " if not last_child else ""

    return output


def get_leaves(node: JsonLogicNode) -> List[JsonLogicExpression]:

    if isinstance(node, JsonLogicLeaf):
        return [asdict(node)]

    return sum((get_leaves(child) for child in node.children), [])
