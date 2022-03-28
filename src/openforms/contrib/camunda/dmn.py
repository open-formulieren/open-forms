from typing import Any, Dict

from django_camunda.client import get_client
from django_camunda.utils import deserialize_variable

from .utils import serialize_variables


def evaluate_dmn(
    dmn_key: str, *, dmn_id: str = "", input_values: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate the specified DMN table with the given input values.

    If an ID is provided, the DMN table with the given ID is used. Otherwise, the most
    recent DMN table matching the given key will be evaluated.

    The return value is the output deserialized to Python types.
    """
    client = get_client()
    serialized = serialize_variables(input_values)

    result = ...
    raise NotImplementedError("implement API call")

    return {var: deserialize_variable(value) for var, value in result.items()}
