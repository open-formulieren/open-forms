from typing import Optional

from django.urls import reverse

import elasticapm
from rest_framework.request import Request

from openforms.forms.custom_field_types import handle_custom_types
from openforms.prefill import inject_prefill
from openforms.submissions.models import Submission
from openforms.typing import DataMapping

from .datastructures import FormioConfigurationWrapper
from .dynamic_config.service import apply_dynamic_configuration
from .normalization import normalize_value_for_component
from .typing import Component
from .utils import iter_components, mimetype_allowed
from .variables import inject_variables

__all__ = [
    "get_dynamic_configuration",
    "update_configuration_for_request",
    "normalize_value_for_component",
    "iter_components",
    "mimetype_allowed",
    "inject_variables",
]

from ..config.models import GlobalConfiguration


# TODO: it might be beneficial to memoize this function if it runs multiple times in
# the context of the same request
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
        config_wrapper.configuration, request=request, submission=submission
    )
    assert config_wrapper._cached_component_map is None

    apply_dynamic_configuration(config_wrapper, data=data)
    # prefill is still 'special' even though it uses variables, as we specifically
    # set the `defaultValue` key to the resulting variable.
    # This *could* be refactored in the future by assigning a template expression to
    # the default value key and then pass it through :func:`inject_variables`. However,
    # this is still complicated in the form designer for non-text input defaults such
    # as checkboxes/dropdowns/radios/...
    inject_prefill(config_wrapper, submission)
    return config_wrapper


def update_configuration_for_request(configuration: dict, request: Request) -> None:
    """
    Given a static Formio configuration, apply dynamic changes we always must do, like setting absolute urls.

    The configuration is modified in the context of the provided :arg:`submission`.
    """
    pipeline = (
        update_urls_in_place,
        update_default_file_types,
    )
    for component in iter_components(configuration):
        for function in pipeline:
            function(component, request=request)


def update_urls_in_place(component: Component, request: Request) -> None:
    if component.get("type") == "file":
        component["url"] = request.build_absolute_uri(
            reverse("api:formio:temporary-file-upload")
        )


def update_default_file_types(component: Component, **kwargs) -> None:
    if component.get("type") == "file" and component.get("useConfigFiletypes"):
        config = GlobalConfiguration.get_solo()
        component["filePattern"] = ",".join(config.form_upload_default_file_types)
