"""
Implement component-specific dynamic configuration based on (submission) state.
"""
from typing import Optional

from rest_framework.request import Request

from openforms.submissions.models import Submission
from openforms.typing import DataMapping

from ..datastructures import FormioConfigurationWrapper
from ..registry import register

__all__ = ["rewrite_formio_components", "rewrite_formio_components_for_request"]


def rewrite_formio_components(
    configuration_wrapper: FormioConfigurationWrapper,
    submission: Submission,
    data: Optional[DataMapping] = None,
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
    data = data or {}  # normalize
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
        # prevent multiple overwrites of content components (bandaid for #2895)
        html = component.get("html", None)
        if component["type"] != "content" or (html and "nonce" not in html):
            register.update_config_for_request(component, request=request)
    return configuration_wrapper


def get_translated_custom_error_messages(
    config_wrapper: FormioConfigurationWrapper, submission: Submission
) -> FormioConfigurationWrapper:
    for component in config_wrapper:
        if (
            not (custom_error_messages := component.get("translatedErrors"))
            or "errors" in component
        ):
            continue

        language = submission.language_code
        component["errors"] = custom_error_messages[language]

    return config_wrapper
