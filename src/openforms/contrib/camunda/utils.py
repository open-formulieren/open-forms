from typing import Any, Dict, Optional

from django_camunda.types import ProcessVariables
from django_camunda.utils import serialize_variable


def serialize_variables(variables: Optional[Dict[str, Any]]) -> ProcessVariables:
    if variables is None:
        return {}
    return {key: serialize_variable(value) for key, value in variables.items()}
