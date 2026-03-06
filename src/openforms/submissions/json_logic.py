from json_logic.meta.expressions import (
    JSONLogicExpression,
    destructure,
)
from json_logic.typing import JSON

from ..variables.constants import FormVariableDataTypes
from ..variables.service import resolve_key
from .models.submission_value_variable import SubmissionValueVariablesState

DATA_TYPE_TO_DATA_OPERATOR_MAP = {
    FormVariableDataTypes.date: "date",
    FormVariableDataTypes.datetime: "datetime",
    # FormVariableDataTypes.time: "time",
}


def get_data_type_operator(
    var_key: str, state: SubmissionValueVariablesState
) -> str | None:
    form_variable_key = resolve_key(var_key, state.variables)
    if form_variable_key is None:
        return None

    variable = state.variables[form_variable_key]
    data_type = variable.get_data_type(var_key)

    return DATA_TYPE_TO_DATA_OPERATOR_MAP.get(data_type, None)


def add_data_type_information(
    expression: JSON, state: SubmissionValueVariablesState
) -> JSON:

    if isinstance(expression, list):
        expression_new = [add_data_type_information(expr, state) for expr in expression]
        return expression_new

    if not isinstance(expression, dict):
        return expression

    normalized = JSONLogicExpression.normalize(expression)
    assert isinstance(normalized, dict)
    operator, argument = destructure(normalized)

    match operator:
        case "var":
            assert isinstance(argument, list)
            # We can't add any data type information if the argument is another
            # expression, because we have no data available here.
            var_name = argument[0]
            if not isinstance(var_name, str):
                return normalized

            data_type_operator = get_data_type_operator(var_name, state)
            if data_type_operator is None:
                return normalized

            return {data_type_operator: [normalized]}
        case "map" | "reduce":
            pass
        case "date" | "datetime":
            # It already contains a date operator.
            return normalized
        case _:
            pass

    # Evaluate the argument
    argument_new = add_data_type_information(argument, state)
    return {operator: argument_new}
