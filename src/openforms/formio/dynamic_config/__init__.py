"""
Implement component-specific dynamic configuration based on (submission) state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.request import Request

from formio_types import (
    AddressNL,
    Children,
    Columns,
    Content,
    CosignV1,
    EditGrid,
    Fieldset,
    Partners,
    SoftRequiredErrors,
)
from formio_types._base import SupportedLanguage

from ..datastructures import FormioConfig, FormioConfigurationWrapper, FormioData
from ..registry import register

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


__all__ = ["rewrite_formio_components"]


def rewrite_formio_components(
    config: FormioConfig,
    submission: Submission,
    data: FormioData | None = None,
) -> FormioConfig:
    """
    Loop over the formio configuration and mutate components in place.

    :param config: Container object holding the Formio form configuration
      to be updated (if applicable). The rewriting loops over all components one-by-one
      and applies the changes.
    :param submission: The submission instance for which we are rewriting the
      configurations. This allows you to inspect state and use convenience methods
      that may not be available in the variables data.
    :param data: key-value mapping of variable name to variable value. If a submission
      context is available, the variables of the submission are included here.
    """
    data = data or FormioData()  # normalize
    for component in config:
        replacement = register.update_config(
            component, submission=submission, data=data
        )
        if replacement is not None:
            raise NotImplementedError("handle replacement!")

    return config


def rewrite_formio_components_for_request(
    configuration_wrapper: FormioConfigurationWrapper, request: Request
) -> FormioConfigurationWrapper:
    """
    Loop over the formio configuration and inject request-specific configuration.
    """
    from ..service import _convert_legacy_component, _dump_to_legacy_component

    for component in configuration_wrapper:
        # TODO: lift up the conversion to avoid all these round-trips
        _component = _convert_legacy_component(component)
        register.update_config_for_request(_component, request=request)
        component.update(_dump_to_legacy_component(_component))

    # reset the configuration wrapper because nested components in fieldsets, editgrids
    # and columns will be different instances rather than having been mutated due to
    # using msgspec.to_builtins(...)
    # TODO: remove this when the msgspec machinery is lifted all the way to the top
    configuration_wrapper._cached_component_map = None

    return configuration_wrapper


def get_translated_custom_error_messages(
    config: FormioConfig, language_code: str
) -> FormioConfig:
    # TODO: defer this to the component registry?
    for component in config:
        # the generic mechanism looks up errors in the ``translated_errors`` attribute,
        # but shouldn't do any additional work if ``errors`` is already assigned/resolved
        match component:
            # these component types don't support the ``errors``/``translated_errors``
            # mechanism
            case (
                EditGrid()
                | Fieldset()
                | Columns()
                | Content()
                | SoftRequiredErrors()
                | Partners()
                | Children()
                | CosignV1()
            ):
                pass
            # skip if errors are already assigned/derived
            case _ if (errors := component.errors) or errors is not None:
                pass
            # grab the language-specific error messages if they're available and store
            # them in the resolved errors property
            case _ if errors_by_language_code := component.translated_errors:
                # FIXME: narrow type?
                custom_error_messages = errors_by_language_code.get(language_code)
                if custom_error_messages is not None:
                    # FIXME: doesn't infer the discriminated union -> use registry
                    # instead
                    component.errors = custom_error_messages

        # TODO: move this into component-specific registry

        match component:
            case AddressNL() if component.open_forms and (
                addressnl_components := component.open_forms.components
            ):
                for component_config in (
                    addressnl_components.postcode,
                    addressnl_components.city,
                ):
                    if not component_config:
                        continue
                    if (
                        component_config.errors
                        or not component_config.translated_errors
                    ):
                        continue
                    # FIXME: narrow type?
                    custom_error_messages = component_config.translated_errors.get(
                        language_code
                    )
                    if not custom_error_messages:
                        continue
                    component_config.errors = custom_error_messages

    return config


def localize_components(
    config: FormioConfig,
    language_code: SupportedLanguage,
    enabled: bool = True,
) -> None:
    """
    Apply the configured translations for each component in the configuration.

    .. note:: this function mutates the configuration.
    """
    for component in config:
        register.localize_component(
            component, language_code=language_code, enabled=enabled
        )
