"""
Implement component-specific dynamic configuration based on (submission) state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.request import Request

from ..datastructures import FormioConfigurationWrapper, FormioData
from ..registry import register

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


__all__ = ["rewrite_formio_components", "rewrite_formio_components_for_request"]


def rewrite_formio_components(
    configuration_wrapper: FormioConfigurationWrapper,
    submission: Submission,
    data: FormioData | None = None,
) -> FormioConfigurationWrapper:
    """
    Loop over the formio configuration and mutate components in place.

    :arg configuration_wrapper: Container object holding the Formio form configuration
      to be updated (if applicable). The rewriting loops over all components one-by-one
      and applies the changes.
    :arg submission: The submission instance for which we are rewriting the
      configurations. This allows you to inspect state and use convenience methods
      that may not be available in the variables data.
    :arg data: key-value mapping of variable name to variable value. If a submission
      context is available, the variables of the submission are included here.
    """
    data = data or FormioData()  # normalize
    for component in configuration_wrapper:
        register.update_config(component, submission=submission, data=data)
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


def get_translated_custom_error_messages(
    config_wrapper: FormioConfigurationWrapper, language_code: str
) -> FormioConfigurationWrapper:
    for component in config_wrapper:
        if (
            not (custom_error_messages := component.get("translatedErrors"))
            or "errors" in component
        ):
            continue

        component["errors"] = custom_error_messages[language_code]

    return config_wrapper


def localize_components(
    configuration_wrapper: FormioConfigurationWrapper,
    language_code: str,
    enabled: bool = True,
) -> None:
    """
    Apply the configured translations for each component in the configuration.

    .. note:: this function mutates the configuration.
    """
    for component in configuration_wrapper:
        register.localize_component(
            component, language_code=language_code, enabled=enabled
        )
