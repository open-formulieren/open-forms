from __future__ import annotations

from json_logic import jsonLogic
from json_logic.typing import JSON

from openforms.typing import VariableValue


def partially_evaluate_json_logic(
    expression: JSON, data: dict[str, VariableValue]
) -> tuple[VariableValue, bool]:
    """
    Partially evaluate a JSON logic expression.

    Depending on the available data, the variable operators will be substituted with the
    values, and evaluted where possible.

    Our custom date-related operators ('date', 'datetime', 'today', 'rdelta', and
    'duration') will not be evaluated individually, but only if the entire expression
    can be resolved. This is to avoid (possibly) creating a mix between JSON primitives
    and date-related objects.

    The following operations are not supported (by `jsonLogic`): 'filter', 'all',
    'some', 'none', and 'substr'.

    An example:
    >>> expression, resolved = partially_evaluate_json_logic(
    ...     {"+": [{"var": "foo"}, {"var": "bar"}]}, {"foo": 1}
    ... )
    >>> print(expression)
    {"+": [1, {"var": "bar"}]}

    :param expression: JSON logic expression.
    :param data: Available data, which should support nested-data access through the use
      of periods in keys.
    :return: Tuple of the (partially) evaluated JSON logic expression and a flag
      indicating whether the expression was fully resolved. Note that it could return a
      date or datetime object if the expression was evalutated completely.
    """
    if not isinstance(expression, dict):
        return expression, True

    assert len(expression) == 1, "Expression must only have a single operator"
    operator, argument = next(iter(expression.items()))

    match operator:
        case "var":
            # Argument could be a list, in which case `jsonLogic` just selects the first
            # value.
            if isinstance(argument, list):
                argument = argument[0]
            assert isinstance(argument, str)

            top_level = argument.split(".")[0]
            # Return the value if the top-level key is available, otherwise the
            # expression should stay as is.
            if top_level in data:
                return data.get(argument), True
            else:
                return {operator: argument}, False
        case "map" | "reduce":
            # Map and reduce operations have a fixed order of arguments:
            # 1. Variable operation (must be an array)
            # 2. Operation to perform on each array item(s)
            # 3. Initial value (for reduce only, and cannot be a variable expression)
            assert isinstance(argument, list)
            var_operation = argument[0]
            # Note that one could create a logic rule with a list of numbers (e.g.
            # `[1,2,3]`) instead of a variable operation, but that doesn't make much
            # sense to do. The desired computed value should just be inserted directly
            # in that case.
            assert (
                isinstance(var_operation, dict)
                and len(var_operation) == 1
                and "var" in var_operation
            )
            assert isinstance(var_operation["var"], str)
            # Both operations only take a single variable, which we cannot substitute
            # with the actual value, because `jsonLogic` will see dict array items as
            # operations. So, we either evaluate the whole expression, or we do nothing.
            if var_operation["var"] not in data:
                return {operator: argument}, False
            else:
                return jsonLogic({operator: argument}, data), True
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
            return {operator: argument}, True
        case _:
            pass

    if isinstance(argument, dict):
        # The argument is another operator
        argument_new, fully_resolved = partially_evaluate_json_logic(argument, data)
    else:
        assert isinstance(argument, list), "argument not a list"

        fully_resolved = True
        argument_new = []
        for arg in argument:
            arg_new, resolved = partially_evaluate_json_logic(arg, data)
            argument_new.append(arg_new)
            fully_resolved = fully_resolved and resolved

    if fully_resolved:
        return jsonLogic({operator: argument_new}, data), True
    else:
        return {operator: argument_new}, False
