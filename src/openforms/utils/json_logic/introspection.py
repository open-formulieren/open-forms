"""
Introspection of JsonLogic expression, based on our json_logic.meta extension.
"""

from json_logic.meta import JSONLogicExpression
from json_logic.typing import JSON

from .datastructures import ExpressionIntrospection
from .descriptions import (
    DescriptionGeneratorProtocol,
    op_and,
    op_bool,
    op_cat,
    op_date,
    op_datetime,
    op_division,
    op_equal,
    op_greater_than,
    op_greater_than_or_equal,
    op_if,
    op_in,
    op_less_than,
    op_less_than_or_equal,
    op_map,
    op_max,
    op_merge,
    op_min,
    op_missing,
    op_missing_some,
    op_modulo,
    op_multiply,
    op_not,
    op_not_equal,
    op_or,
    op_rdelta,
    op_reduce,
    op_subtraction,
    op_sum,
    op_today,
    op_var,
)

__all__ = [
    "OPERATION_DESCRIPTION_BUILDERS",
    "introspect_json_logic",
    "generate_rule_description",
]


OPERATION_DESCRIPTION_BUILDERS: dict[str, DescriptionGeneratorProtocol] = {
    "var": op_var,
    "missing": op_missing,
    "missing_some": op_missing_some,
    "==": op_equal,
    "===": op_equal,
    "!=": op_not_equal,
    "!==": op_not_equal,
    ">": op_greater_than,
    "<": op_less_than,
    ">=": op_greater_than_or_equal,
    "<=": op_less_than_or_equal,
    "!": op_not,
    "!!": op_bool,
    "%": op_modulo,
    "and": op_and,
    "or": op_or,
    "?:": op_if,
    "if": op_if,
    "in": op_in,
    "cat": op_cat,
    "+": op_sum,
    "*": op_multiply,
    "-": op_subtraction,
    "/": op_division,
    "min": op_min,
    "max": op_max,
    "merge": op_merge,
    "reduce": op_reduce,
    "map": op_map,
    # custom operators
    "today": op_today,
    "date": op_date,
    "datetime": op_datetime,
    "rdelta": op_rdelta,
}


def introspect_json_logic(expression: JSON) -> ExpressionIntrospection:
    tree = JSONLogicExpression.from_expression(expression).as_tree()
    return ExpressionIntrospection(expression=expression, tree=tree)


def generate_rule_description(expression: JSON) -> str:
    introspection = introspect_json_logic(expression)
    return introspection.description
