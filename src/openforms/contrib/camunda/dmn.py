import logging
from typing import Any, Dict

from django_camunda.client import get_client
from django_camunda.utils import deserialize_variable

from .utils import serialize_variables

logger = logging.getLogger(__name__)


def evaluate_dmn(
    dmn_key: str, *, dmn_id: str = "", input_values: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate the specified DMN table with the given input values.

    If an ID is provided, the DMN table with the given ID is used. Otherwise, the most
    recent DMN table matching the given key will be evaluated.

    The return value is the output deserialized to Python types.
    """
    logger.debug(
        "Evaluating DMN table with key %s and dmn_id %s",
        dmn_key,
        dmn_id,
    )
    client = get_client()
    serialized = serialize_variables(input_values)

    result = client.post(
        f"decision-definition/key/{dmn_key}/evaluate",
        json={"variables": serialized},
    )

    output_variables = {}
    for output in result:
        for key, value in output.items():
            output_variables[key] = deserialize_variable(value)

    return output_variables
