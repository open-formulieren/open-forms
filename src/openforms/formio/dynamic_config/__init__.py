"""
Implement component-specific dynamic configuration based on (submission) state.

This will eventually replace ``openforms.forms.custom_field_types``.
"""
from typing import Optional

from openforms.typing import DataMapping

from ..datastructures import FormioConfigurationWrapper
from ..registry import register

__all__ = ["apply_dynamic_configuration"]


def apply_dynamic_configuration(
    configuration_wrapper: FormioConfigurationWrapper,
    data: Optional[DataMapping] = None,
) -> FormioConfigurationWrapper:
    """
    Loop over the formio configuration and mutate components in place.
    """
    data = data or {}  # normalize
    for component in configuration_wrapper:
        register.update_config(component, data=data)
    return configuration_wrapper
