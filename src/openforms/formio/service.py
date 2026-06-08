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

from opentelemetry import trace

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
from .visibility import is_hidden, process_visibility

if TYPE_CHECKING:
    from openforms.submissions.models import Submission

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
    "is_hidden",
]

tracer = trace.get_tracer("openforms.formio.service")


def format_value(component: Component, value: Any, *, as_html: bool = False):
    """
    Format a submitted value in a way that is most appropriate for the component type.
    """
    return register.format(component, value, as_html=as_html)


def normalize_value_for_component(component: Component, value: Any) -> Any:
    """
    Given a value (actual or default value) and the component, apply the component-
    specific normalization.
    """
    return register.normalize(component, value)


def holds_submission_data(component: Component) -> bool:
    """Return whether data can be submitted for a particular component."""
    return register.holds_submission_data(component)


def get_component_datatype(component: Component) -> FormVariableDataTypes:
    """
    Get the intrinsic data type for a particular component.
    """
    return register.get_component_data_type(component)


def get_component_data_subtype(
    component: Component,
) -> Literal[""] | FormVariableDataTypes:
    """
    Get the data subtype of a component.

    :returns: The underlying data type of the component if the component is configured
      as ``multiple`` or intrinsically has an array data type. Otherwise, an empty
      string is returned to signal the data subtype is not applicable.
    """
    return register.get_component_data_subtype(component)


def get_component_empty_value(component: Component) -> JSONValue:
    """
    Get the component-specific empty value.
    """
    return register.get_empty_value(component)


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
    return _build_serializer(components, register=_register or register, **kwargs)


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
    return registry.as_json_data(component, value)


def as_json_schema(
    component: Component, _register: ComponentRegistry | None = None
) -> JSONObject | list[JSONObject] | None:
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
    return registry.as_json_schema(component)
