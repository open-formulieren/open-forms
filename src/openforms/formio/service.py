"""
Expose the public openforms.formio Python API.

The service module exposes the functions/utilities that may be used by other Django
apps/packages:

* Try to keep this module stable and avoid breaking changes - extensions may rely on this!
* Keep it small! The actual implementation should be done in specialized subpackages or
  submodules and only their 'public' API should be imported and used.
"""
from typing import Any, Optional

import elasticapm
from rest_framework.request import Request

from openforms.forms.custom_field_types import handle_custom_types
from openforms.prefill import inject_prefill
from openforms.submissions.models import Submission
from openforms.typing import DataMapping

from .datastructures import FormioConfigurationWrapper
from .dynamic_config import (
    rewrite_formio_components,
    rewrite_formio_components_for_request,
)
from .registry import register
from .typing import Component
from .utils import iter_components
from .variables import inject_variables

__all__ = [
    "get_dynamic_configuration",
    "normalize_value_for_component",
    "iter_components",
    "inject_variables",
    "format_value",
    "rewrite_formio_components_for_request",
]


def format_value(component: Component, value: Any, as_html: bool = False):
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
    data: Optional[DataMapping] = None,
) -> FormioConfigurationWrapper:
    """
    Given a static Formio configuration, apply the hooks to dynamically transform this.

    The configuration is modified in the context of the provided :arg:`submission`.
    """
    # TODO: see if we can make the config wrapper smart enough to deal with this
    config_wrapper.configuration = handle_custom_types(
        config_wrapper.configuration, submission=submission
    )

    rewrite_formio_components(config_wrapper, data=data)

    # prefill is still 'special' even though it uses variables, as we specifically
    # set the `defaultValue` key to the resulting variable.
    # This *could* be refactored in the future by assigning a template expression to
    # the default value key and then pass it through :func:`inject_variables`. However,
    # this is still complicated in the form designer for non-text input defaults such
    # as checkboxes/dropdowns/radios/...
    inject_prefill(config_wrapper, submission)
    return config_wrapper
