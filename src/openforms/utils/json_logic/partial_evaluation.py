from __future__ import annotations

from json_logic import jsonLogic
from json_logic.meta.expressions import (
    JSONLogicExpression,
    destructure,
)
from json_logic.typing import JSON

from openforms.typing import VariableValue


def partially_evaluate_json_logic(
    expression: JSON, data: dict[str, VariableValue]
) -> tuple[VariableValue, bool]:
    """
    Partially evaluate a JSON logic expression.

    Depending on the available data, the variable operators will be substituted with the
    values, and evaluated where possible.

    Our custom date-related operators ('date', 'datetime', 'today', 'rdelta', and
    'duration') will not be evaluated individually, but only if the (sub) expression
    can be resolved. This is to avoid (possibly) creating a mix between JSON primitives
    and date-related objects, and in turn changing the behavior of the expression.

    The following operations are not supported (by `jsonLogic`): 'filter', 'all',
    'some', 'none', and 'substr'.

    An example (note that we apply a normalization to wrap all arguments of an operator
    in a list):
    >>> expression, resolved = partially_evaluate_json_logic(
    ...     {"+": [{"var": "foo"}, {"var": "bar"}]}, {"foo": 1}
    ... )
    >>> print(expression)
    {"+": [1, {"var": ["bar"]}]}

    :param expression: JSON logic expression.
    :param data: Available data, which should support nested-data access through the use
      of periods in keys.
    :return: Tuple of the (partially) evaluated JSON logic expression and a flag
      indicating whether the expression was fully resolved. Note that it could return a
      date or datetime object if the expression was evalutated completely.
    """
    if isinstance(expression, list):
        fully_resolved = True
        expression_new = []
        for expr in expression:
            expr_new, resolved = partially_evaluate_json_logic(expr, data)
            expression_new.append(expr_new)
            fully_resolved = fully_resolved and resolved
        return expression_new, fully_resolved

    if not isinstance(expression, dict):
        return expression, True

    normalized = JSONLogicExpression.normalize(expression)
    assert isinstance(normalized, dict)
    operator, argument = destructure(normalized)

    match operator:
        case "var":
            # With the expression being normalized, it has to be a list.
            assert isinstance(argument, list)

            # It could be a nested expression
            argument_new, resolved = partially_evaluate_json_logic(argument, data)

            # Return the value the argument was resolved and the key is available,
            # otherwise the expression should stay as is.
            assert isinstance(argument_new, list)
            if resolved and argument_new[0] in data:
                assert isinstance(argument_new[0], str)
                return data.get(argument_new[0]), True
            else:
                return {operator: argument_new}, False
        case "map" | "reduce":
            # Map and reduce operations have a fixed order of arguments:
            # 1. Variable operation (must be an array)
            # 2. Operation to perform on each array item(s)
            # 3. Initial value (for reduce only, and cannot be a variable expression)
            assert isinstance(argument, list)
            var_operation_new, resolved = partially_evaluate_json_logic(
                argument[0], data
            )
            # Both operations only take a single variable, which we cannot substitute
            # with the actual value, because `jsonLogic` will see dict array items as
            # operations. So, we either evaluate the whole expression, or we do nothing.
            if resolved:
                return jsonLogic(expression, data), True
            else:
                # Mismatch between the `JSON` type of `json_logic`, and our own
                # `JSONValue`
                argument[0] = var_operation_new  # pyright: ignore[reportCallIssue, reportArgumentType]
                return expression, False  # pyright: ignore[reportReturnType]
        case "rdelta":
            assert isinstance(argument, list)
            # The argument of the "rdelta" operator is a list, which can contain
            # variable expressions. We should not evaluate the "rdelta" operator
            # directly, though, but only if the entire expression was resolved at the
            # end.
            fully_resolved = True
            argument_new = []
            for arg in argument:
                arg_new, resolved = partially_evaluate_json_logic(arg, data)
                argument_new.append(arg_new)
                fully_resolved = fully_resolved and resolved
            return {operator: argument_new}, fully_resolved
        case "date" | "datetime" | "duration":
            # These operators should not be evaluated directly, but only if the entire
            # expression was resolved at the end. Their arguments could still contain
            # variable expressions, though.
            argument_new, resolved = partially_evaluate_json_logic(argument, data)
            return {operator: argument_new}, resolved
        case "today":
            # For the "today" operator, the arguments are ignored, so we just return an
            # unchanged expression, which can be evaluated at the end.
            # Mismatch between the `JSON` type of `json_logic`, and our own
            # `JSONValue`
            return expression, True  # pyright: ignore[reportReturnType]
        case _:
            pass

    # Evaluate the argument
    argument_new, fully_resolved = partially_evaluate_json_logic(argument, data)

    if fully_resolved:
        return jsonLogic({operator: argument_new}, data), True
    else:
        return {operator: argument_new}, False
