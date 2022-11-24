"""
Implement component-specific dynamic configuration based on (submission) state.

This will eventually replace ``openforms.forms.custom_field_types``.
"""
from typing import Optional

from rest_framework.request import Request

from openforms.typing import DataMapping

from ..datastructures import FormioConfigurationWrapper
from ..registry import register

__all__ = ["rewrite_formio_components", "rewrite_formio_components_for_request"]


def rewrite_formio_components(
    configuration_wrapper: FormioConfigurationWrapper,
    data: Optional[DataMapping] = None,
) -> FormioConfigurationWrapper:
    """
    Loop over the formio configuration and mutate components in place.

    :arg configuration_wrapper: Container object holding the Formio form configuration
      to be updated (if applicable). The rewriting loops over all components one-by-one
      and applies the changes.
    :arg data: key-value mapping of variable name to variable value. If a submission
      context is available, the variables of the submission are included here.
    :arg request: The HTTP request received by the API view when rewriting is done as
      part of an HTTP request-response cycle. This is ``None`` otherwise (e.g. in
      background tasks).
    """
    data = data or {}  # normalize
    for component in configuration_wrapper:
        register.update_config(component, data=data)
    return configuration_wrapper


def rewrite_formio_components_for_request(
    configuration_wrapper: FormioConfigurationWrapper, request: Request
) -> FormioConfigurationWrapper:
    """
    Loop over the formio configuration and inject request-specific configuration.
    """
    for component in configuration_wrapper:
        register.update_config_for_request(component, request=request)
    return configuration_wrapper
