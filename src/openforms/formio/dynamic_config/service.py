"""
Public API for dynamic configuration.
"""
from typing import Optional

from openforms.typing import DataMapping, JSONObject

from .registry import register

__all__ = ["apply_dynamic_configuration"]


def apply_dynamic_configuration(
    configuration: JSONObject, data: Optional[DataMapping] = None
) -> JSONObject:
    """
    Loop over the formio configuration and mutate components in place.
    """
    from ..service import iter_components

    data = data or {}  # normalize
    for component in iter_components(configuration, recursive=True):
        register.update_config(component, data=data)
    return configuration
