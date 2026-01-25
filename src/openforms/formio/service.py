"""
Expose the public openforms.formio Python API.

The service module exposes the functions/utilities that may be used by other Django
apps/packages:

* Try to keep this module stable and avoid breaking changes - extensions may rely on this!
* Keep it small! The actual implementation should be done in specialized subpackages or
  submodules and only their 'public' API should be imported and used.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from django.utils.safestring import SafeString

import msgspec
import structlog
from opentelemetry import trace

from formio_types import AnyComponent
from formio_types.datetime import FormioDateTime
from openforms.typing import JSONObject, JSONValue, VariableValue
from openforms.variables.constants import FormVariableDataTypes

from .datastructures import DuplicateKeyError, FormioConfigurationWrapper, FormioData
from .dynamic_config import (
    get_translated_custom_error_messages,
    localize_components,
    rewrite_formio_components,
    rewrite_formio_components_for_request,
)
from .registry import ComponentRegistry, register
from .serializers import build_serializer as _build_serializer
from .typing import Component
from .utils import (
    get_readable_path_from_configuration_path,
    iter_components,
    iterate_data_with_components,
)
from .variables import extract_variables_from_template_properties, inject_variables
from .visibility import process_visibility

if TYPE_CHECKING:
    from openforms.submissions.models import Submission

logger = structlog.stdlib.get_logger()

__all__ = [
    "DuplicateKeyError",
    "extract_variables_from_template_properties",
    "get_dynamic_configuration",
    "normalize_value_for_component",
    "iter_components",
    "inject_variables",
    "format_value",
    "rewrite_formio_components_for_request",
    "FormioConfigurationWrapper",
    "FormioData",
    "iterate_data_with_components",
    "build_serializer",
    "rewrite_formio_components",
    "as_json_data",
    "as_json_schema",
    "process_visibility",
    "get_component_empty_value",
    "get_readable_path_from_configuration_path",
    "holds_submission_data",
]

tracer = trace.get_tracer("openforms.formio.service")


def _fixup_component_properties(type_: type, obj: Any):
    if type_ is FormioDateTime:
        return FormioDateTime.fromstr(obj)
    return obj


def _convert_legacy_component(component: Component) -> AnyComponent:
    try:
        _component: AnyComponent = msgspec.convert(
            component,
            type=AnyComponent,
            dec_hook=_fixup_component_properties,
        )
    except msgspec.ValidationError as exc:
        logger.exception(
            "component_conversion_failure",
            type=component.get("type", "unknown"),
            key=component.get("key", "unknown"),
            exc_info=exc,
        )
        raise
    return _component


def _enc_hook(obj: Any) -> Any:
    match obj:
        case SafeString():
            # slice the string, because SafeString is a subclass of string and this is the
            # only way to evaluate it
            return obj[:]
        case FormioDateTime():
            return obj.actual_value
        case _:
            # Raise a NotImplementedError for other types
            raise NotImplementedError(f"Objects of type {type(obj)} are not supported")


def dump_to_legacy(obj: Any):
    return msgspec.to_builtins(obj, enc_hook=_enc_hook)


def _dump_to_legacy_component(component: AnyComponent):
    return dump_to_legacy(component)


def format_value(component: Component, value: Any, *, as_html: bool = False):
    """
    Format a submitted value in a way that is most appropriate for the component type.
    """
    _component = _convert_legacy_component(component)
    return register.format(_component, value, as_html=as_html)


def normalize_value_for_component(component: Component, value: Any) -> Any:
    """
    Given a value (actual or default value) and the component, apply the component-
    specific normalization.
    """
    _component = _convert_legacy_component(component)
    return register.normalize(_component, value)


def holds_submission_data(component: Component) -> bool:
    """Return whether data can be submitted for a particular component."""
    _component = _convert_legacy_component(component)
    return register.holds_submission_data(_component)


def get_component_datatype(component: Component) -> FormVariableDataTypes:
    """
    Get the intrinsic data type for a particular component.
    """
    _component = _convert_legacy_component(component)
    return register.get_component_data_type(_component)


def get_component_data_subtype(
    component: Component,
) -> Literal[""] | FormVariableDataTypes:
    """
    Get the data subtype of a component.

    :returns: The underlying data type of the component if the component is configured
      as ``multiple`` or intrinsically has an array data type. Otherwise, an empty
      string is returned to signal the data subtype is not applicable.
    """
    _component = _convert_legacy_component(component)
    return register.get_component_data_subtype(_component)


def get_component_empty_value(component: Component) -> JSONValue:
    """
    Get the component-specific empty value.
    """
    _component = _convert_legacy_component(component)
    return register.get_empty_value(_component)


@tracer.start_as_current_span(
    name="get-dynamic-configuration",
    attributes={"span.type": "app", "span.subtype": "formio"},
)
def get_dynamic_configuration(
    config_wrapper: FormioConfigurationWrapper,
    submission: Submission,
    data: FormioData | None = None,
) -> FormioConfigurationWrapper:
    """
    Given a static Formio configuration, apply the hooks to dynamically transform this.

    The configuration is modified in the context of the provided ``submission``
    parameter.
    """
    # Avoid circular imports
    from openforms.prefill.service import inject_prefill

    rewrite_formio_components(config_wrapper, submission=submission, data=data)

    # Add to each component the custom errors in the current locale
    get_translated_custom_error_messages(config_wrapper, submission.language_code)
    localize_components(
        config_wrapper,
        submission.language_code,
        enabled=submission.form.translation_enabled,
    )

    # prefill is still 'special' even though it uses variables, as we specifically
    # set the `defaultValue` key to the resulting variable.
    # This *could* be refactored in the future by assigning a template expression to
    # the default value key and then pass it through :func:`inject_variables`. However,
    # this is still complicated in the form designer for non-text input defaults such
    # as checkboxes/dropdowns/radios/...
    inject_prefill(config_wrapper, submission)

    # reset cache... the hooks above mutate stuff and references are broken that way.
    # TODO: fix before merging msgspec branch!
    config_wrapper._cached_component_map = None
    return config_wrapper


def build_serializer(
    components: Sequence[Component],
    _register: ComponentRegistry | None = None,
    **kwargs,
):
    """
    Translate a sequence of Formio.js component definitions into a serializer.

    This recursively builds up the serializer fields for each (nested) component and
    puts them into a serializer instance ready for validation.
    """
    _components: Sequence[AnyComponent] = msgspec.convert(
        components,
        type=Sequence[AnyComponent],
        dec_hook=_fixup_component_properties,
    )
    return _build_serializer(_components, register=_register or register, **kwargs)


def as_json_data(
    component: Component,
    value: VariableValue,
    _register: ComponentRegistry | None = None,
) -> VariableValue:
    """
    Prepare the raw component value for output as JSON data.

    :param component: The component instance to as context for the variable value.
      Component configuration/options may influence the resulting value.
    :param _register: Optional component registry to use. If no registry was provided,
      the default registry will be used.
    :returns: The same value if no processing is necessary, or an updated/modified value
      to make it suitable for export to JSON (e.g. stripped from internal data).
    """
    registry = _register or register
    _component = _convert_legacy_component(component)
    return registry.as_json_data(_component, value)


def as_json_schema(
    component: Component | AnyComponent, _register: ComponentRegistry | None = None
) -> JSONObject | Sequence[JSONObject] | None:
    """
    Return a JSON schema of a component.

    A description will be added if it is available.

    :param component: The component instance to generate a schema for. Component
      configuration/options influence the resulting schema.
    :param _register: Optional component registry to use. If no registry was provided,
      the default registry will be used.
    :returns: None for leaf-node components that don't produce a value, a list of
      JSON objects intermediate layout components with child nodes or a single
      JSON object otherwise.
    """
    registry = _register or register
    _component = (
        _convert_legacy_component(component)
        if isinstance(component, dict)
        else component
    )
    return registry.as_json_schema(_component)
