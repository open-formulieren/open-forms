"""
Expose the public openforms.formio Python API.

The service module exposes the functions/utilities that may be used by other Django
apps/packages:

* Try to keep this module stable and avoid breaking changes - extensions may rely on this!
* Keep it small! The actual implementation should be done in specialized subpackages or
  submodules and only their 'public' API should be imported and used.
"""

from typing import Any

import elasticapm
from rest_framework.request import Request

from openforms.submissions.models import Submission
from openforms.typing import DataMapping, JSONObject

from .datastructures import FormioConfigurationWrapper, FormioData
from .dynamic_config import (
    get_translated_custom_error_messages,
    localize_components,
    rewrite_formio_components,
    rewrite_formio_components_for_request,
)
from .registry import ComponentRegistry, register
from .serializers import build_serializer as _build_serializer
from .typing import Component
from .utils import iter_components, iterate_data_with_components, recursive_apply
from .variables import inject_variables

__all__ = [
    "get_dynamic_configuration",
    "normalize_value_for_component",
    "iter_components",
    "inject_variables",
    "format_value",
    "rewrite_formio_components_for_request",
    "FormioData",
    "iterate_data_with_components",
    "recursive_apply",
    "build_serializer",
    "rewrite_formio_components",
    "as_json_schema",
]


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


@elasticapm.capture_span(span_type="app.formio")
def get_dynamic_configuration(
    config_wrapper: FormioConfigurationWrapper,
    request: Request,
    submission: Submission,
    data: DataMapping | None = None,
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
    get_translated_custom_error_messages(config_wrapper, submission)
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
    components: list[Component], _register: ComponentRegistry | None = None, **kwargs
):
    """
    Translate a sequence of Formio.js component definitions into a serializer.

    This recursively builds up the serializer fields for each (nested) component and
    puts them into a serializer instance ready for validation.
    """
    return _build_serializer(components, register=_register or register, **kwargs)


def as_json_schema(
    component: Component, _register: ComponentRegistry | None = None
) -> JSONObject:
    """Return a JSON schema of a component.

    :param component: Component
    :param _register: ComponentRegistry | None
    :returns: JSONObject
    """
    registry = _register or register

    component_plugin = registry[component["type"]]
    return component_plugin.as_json_schema(component)
