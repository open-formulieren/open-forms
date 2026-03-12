from collections.abc import Mapping

from json_logic.meta.expressions import (
    JSONLogicExpression,
    destructure,
)
from json_logic.typing import JSON

from openforms.variables.constants import FormVariableDataTypes
from openforms.variables.service import resolve_key

from .models import SubmissionValueVariablesState

DATA_TYPE_TO_DATA_OPERATOR_MAP: Mapping[str, str] = {
    FormVariableDataTypes.date: "date",
    FormVariableDataTypes.datetime: "datetime",
}


def _get_data_type_operator(
    var_key: str, state: SubmissionValueVariablesState
) -> str | None:
    """Get a data-type operator from a data-access key."""
    variables = {**state.variables, **state.static_variables}

    form_variable_key = resolve_key(var_key, variables)
    if form_variable_key is None:
        return None

    variable = variables[form_variable_key]
    if (data_type := variable.get_data_type(var_key)) is not None:
        return DATA_TYPE_TO_DATA_OPERATOR_MAP.get(data_type, None)

    return None


def add_data_type_information(
    expression: JSON,
    state: SubmissionValueVariablesState,
    parent_key: str | None = None,
    in_reduce: bool = False,
) -> JSON:
    """
    Add data-type information to a JSON logic expression.

    Searches the expression for variable operations, and wraps them with the relevant
    data-type operator were applicable.

    For example (consider a form with a date component "dateField"):
    >>> expression = {"==": [{"var": "dateField"}, {"date": "2026-03-10"}]}
    >>> result = add_data_type_information(
    ...     expression, submission.load_submission_value_variables_state()
    ... )
    >>> print(result)
    {"==" [{"date": [{"var": ["dateField"]}]}, {"date": ["2026-03-10"]}]}

    Note that a normalization to wrap all arguments of an operator in a list is applied
    here.

    :param expression: JSON logic expression
    :param state: Submission value variables state, used to get the data-type
      information from.
    :param parent_key: Parent variable name, passed when processing array
      operations (map and reduce).
    :param in_reduce: Flag indicating whether we are inside a reduce operation.
    :return: JSON logic expression with added data-type information.
    """
    # Recursively process the expression.
    if isinstance(expression, list):
        expression_new = [
            add_data_type_information(expr, state, parent_key, in_reduce)
            for expr in expression
        ]
        return expression_new

    # Expression is a primitive.
    if not isinstance(expression, dict):
        return expression

    # Apply normalization.
    normalized = JSONLogicExpression.normalize(expression)
    assert isinstance(normalized, dict)
    operator, argument = destructure(normalized)
    assert isinstance(argument, list)

    match operator:
        case "var":
            var_name = argument[0]
            # We can't add any data type information if the argument is another
            # (variable) expression, because we have no data available here.
            if not isinstance(var_name, str):
                return normalized  # pyright: ignore[reportReturnType]

            # The reduce item expression only has access to variables "current" and
            # "accumulator", where "current" can access individual items of the array
            # using dot notation, e.g. "current.date". Before determining the data type
            # operator, we need to strip "current." from it.
            if in_reduce:
                if var_name == "accumulator":
                    return normalized  # pyright: ignore[reportReturnType]
                var_name = var_name.removeprefix("current").lstrip(".")

            # The array operations access each item individually, but "parent.var_name"
            # is not a valid data-access key, so we create one ourselves :poop:
            # If `var_name` is an empty string, it means the variable was either
            # "current" (reduce operation) or "" (map operation), so we just add a
            # single index to the parent.
            if parent_key:
                var_name = (
                    f"{parent_key}.0.{var_name}" if var_name else f"{parent_key}.0"
                )

            data_type_operator = _get_data_type_operator(var_name, state)
            if data_type_operator is None:
                return normalized  # pyright: ignore[reportReturnType]

            return {data_type_operator: [normalized]}  # pyright: ignore[reportReturnType]
        case "reduce":
            assert len(argument) == 3
            var_expression = add_data_type_information(argument[0], state)
            # We can only determine the data type if we have a (non-nested) variable
            # expression.
            parent = None
            if isinstance(var_expression, dict) and "var" in var_expression:
                assert isinstance(var_expression["var"], list)  # normalized
                if isinstance(var_expression["var"][0], str):
                    parent = var_expression["var"][0]

            item_expression = add_data_type_information(
                argument[1], state, parent, in_reduce=True
            )
            return {operator: [var_expression, item_expression, argument[2]]}
        case "map":
            assert len(argument) == 2
            var_expression = add_data_type_information(argument[0], state, parent_key)
            # We can only determine the data type if we have a (non-nested) variable
            # expression.
            parent = None
            if isinstance(var_expression, dict) and "var" in var_expression:
                assert isinstance(var_expression["var"], list)  # normalized
                if isinstance(var_expression["var"][0], str):
                    parent = var_expression["var"][0]

            item_expression = add_data_type_information(argument[1], state, parent)
            return {
                operator: [var_expression, item_expression],
            }
        case "date" | "datetime":
            # It already contains a date operator.
            return normalized  # pyright: ignore[reportReturnType]
        case _:
            pass

    # Evaluate the argument
    argument_new = add_data_type_information(argument, state, parent_key, in_reduce)
    return {operator: argument_new}
