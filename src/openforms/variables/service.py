"""
Public Python API to access (static) form variables.
"""

from openforms.forms.models import FormVariable
from openforms.plugins.registry import BaseRegistry
from openforms.submissions.models import Submission
from openforms.typing import JSONObject

from .base import BaseStaticVariable
from .constants import FormVariableDataTypes
from .registry import register_static_variable as static_variables_registry
from .utils import get_variables_for_context

__all__ = [
    "get_json_schema_for_user_defined_variable",
    "get_static_variables",
    "get_variables_for_context",
]


type VariablesRegistry = BaseRegistry[BaseStaticVariable]


def get_static_variables(
    *,
    submission: Submission | None = None,
    variables_registry: VariablesRegistry | None = None,
) -> list[FormVariable]:
    """
    Return the full collection of static variables registered by all apps.

    :param submission: Optional, but recommended - the submission instance to get the
      variables for. Many of the static variables require the submission for sufficient
      context to be able to produce a value. Variables are static within that submission
      context, i.e. they don't change because of filling out the form.
    :param variables_registry: The static variables registry to use. If not provided,
      the default registry will be used.

    You should not rely on the order of returned variables, as they are registered in
    the order the Django apps are loaded - and this may change without notice.
    """
    if variables_registry is None:
        variables_registry = static_variables_registry
    return [
        registered_variable.get_static_variable(submission=submission)
        for registered_variable in variables_registry
    ]


# TODO-4980: can be combined with get_json_schema_from_form_variable?
def get_json_schema_for_user_defined_variable(
    data_type: FormVariableDataTypes,
) -> JSONObject:
    """Return the JSON schema definition for a user-defined variable, depending on the
    data type

    :param data_type: The data type of the variable
    """
    match data_type:
        case FormVariableDataTypes.string:
            return {"type": "string"}
        case FormVariableDataTypes.boolean:
            return {"type": "boolean"}
        case FormVariableDataTypes.object:
            return {"type": "object"}
        case FormVariableDataTypes.array:
            return {"type": "array"}
        case FormVariableDataTypes.int:
            return {"type": "integer"}
        case FormVariableDataTypes.float:
            return {"type": "number"}
        case FormVariableDataTypes.datetime:
            return {"type": "string", "format": "date-time"}
        case FormVariableDataTypes.date:
            return {"type": "string", "format": "date"}
        case FormVariableDataTypes.time:
            return {"type": "string", "format": "time"}
        case _:  # pragma: no cover
            raise NotImplementedError(f"Unrecognized data type: {data_type}")
