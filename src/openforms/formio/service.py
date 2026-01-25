"""
Expose the public openforms.formio Python API.

The service module exposes the functions/utilities that may be used by other Django
apps/packages:

* Try to keep this module stable and avoid breaking changes - extensions may rely on this!
* Keep it small! The actual implementation should be done in specialized subpackages or
  submodules and only their 'public' API should be imported and used.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any, Protocol

import elasticapm
import msgspec
import structlog

from formio_types import (
    TYPE_TO_TAG,
    AnyComponent,
    Columns,
    Content,
    Fieldset,
    SoftRequiredErrors,
)
from formio_types.datetime import FormioDateTime
from openforms.typing import JSONObject

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
from .utils import (
    get_component_empty_value,
    iter_components,
    iterate_data_with_components,
    recursive_apply,
)
from .variables import inject_variables
from .visibility import process_visibility

if TYPE_CHECKING:
    from openforms.submissions.models import Submission

logger = structlog.stdlib.get_logger()

__all__ = [
    "get_dynamic_configuration",
    "normalize_value_for_component",
    "iter_components",
    "inject_variables",
    "format_value",
    "rewrite_formio_components_for_request",
    "FormioConfigurationWrapper",
    "FormioData",
    "iterate_data_with_components",
    "recursive_apply",
    "build_serializer",
    "rewrite_formio_components",
    "as_json_schema",
    "process_visibility",
    "get_component_empty_value",
]


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


def format_value(component: Component, value: Any, *, as_html: bool = False):
    """
    Format a submitted value in a way that is most appropriate for the component type.
    """
    try:
        _component = _convert_legacy_component(component)
    except msgspec.ValidationError:
        return value
    return register.format(_component, value, as_html=as_html)


def normalize_value_for_component(component: Component, value: Any) -> Any:
    """
    Given a value (actual or default value) and the component, apply the component-
    specific normalization.
    """
    try:
        _component = _convert_legacy_component(component)
    except msgspec.ValidationError:
        return value
    return register.normalize(_component, value)


@elasticapm.capture_span(span_type="app.formio")
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


def as_json_schema(
    component: Component | AnyComponent,
    _register: ComponentRegistry | None = None,
) -> JSONObject | Sequence[JSONObject] | None:
    """Return a JSON schema of a component.

    A description will be added if it is available.

    Layout components require some extra attention:
      - Content and softRequiredErrors components do not have any values, so a
        schema does not exist: returns ``None``
      - Columns and fieldset components contain other components for which a JSON schema
        needs to be generated: returns a list of JSON objects with the child component
        key as key and the child component JSON schema as value.

    :param component: Component
    :param _register: Optional component registry to use. If no registry was provided,
      the default registry will be used.
    :returns: None for content and softRequiredErrors components, list of JSON objects
      for columns and fieldsets, and a JSON object otherwise.
    """
    registry = _register or register
    if isinstance(component, dict):
        _component = _convert_legacy_component(component)
    else:
        _component = component

    match _component:
        case Content() | SoftRequiredErrors():
            return None
        case Columns():
            return [
                *itertools.chain.from_iterable(
                    _iter_child_schemas(column) for column in _component.columns
                )
            ]
        case Fieldset():
            return [*_iter_child_schemas(_component)]
        case _:
            component_type = TYPE_TO_TAG[type(_component)]
            component_plugin = registry[component_type]
            schema = component_plugin.as_json_schema(_component)
            if description := getattr(_component, "description", ""):
                schema["description"] = description
            return schema


class ParentComponent(Protocol):
    components: Sequence[AnyComponent]


def _iter_child_schemas(parent: ParentComponent) -> Iterator[JSONObject]:
    """
    Generate the children's schemas.
    """
    for child in parent.components:
        child_schema = as_json_schema(child)
        match child_schema:
            # Layout components produce no schema at all
            case None:
                continue
            # Columns and fieldset components return a list of children
            case Sequence():
                yield from child_schema
            case _:
                # Other components get added to the list as a dict with their key
                yield {child.key: child_schema}
