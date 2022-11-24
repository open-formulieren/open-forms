from typing import Any, Optional

from django.urls import reverse

import elasticapm
from rest_framework.request import Request

from csp_post_processor import post_process_html
from openforms.forms.custom_field_types import handle_custom_types
from openforms.prefill import inject_prefill
from openforms.submissions.models import Submission
from openforms.typing import DataMapping

from .datastructures import FormioConfigurationWrapper
from .dynamic_config import apply_dynamic_configuration
from .registry import register
from .typing import Component
from .utils import iter_components
from .variables import inject_variables

__all__ = [
    "get_dynamic_configuration",
    "update_configuration_for_request",
    "normalize_value_for_component",
    "iter_components",
    "inject_variables",
    "format_value",
]

from ..config.models import GlobalConfiguration


def format_value(component: Component, value: Any, as_html: bool = False):
    return register.format(component, value, as_html=as_html)


def normalize_value_for_component(component: Component, value: Any) -> Any:
    """
    Given a value (actual or default value) and the component, apply the component-
    specific normalization.
    """
    return register.normalize(component, value)


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

    apply_dynamic_configuration(config_wrapper, data=data)
    # prefill is still 'special' even though it uses variables, as we specifically
    # set the `defaultValue` key to the resulting variable.
    # This *could* be refactored in the future by assigning a template expression to
    # the default value key and then pass it through :func:`inject_variables`. However,
    # this is still complicated in the form designer for non-text input defaults such
    # as checkboxes/dropdowns/radios/...
    inject_prefill(config_wrapper, submission)
    return config_wrapper


def update_configuration_for_request(
    config_wrapper: FormioConfigurationWrapper, request: Request
) -> None:
    """
    Given a static Formio configuration, apply dynamic changes we always must do, like setting absolute urls.

    The configuration is modified in the context of the provided :arg:`submission`.
    """

    # TODO move this to openforms.formio.dynamic_config
    pipeline = (
        update_urls_in_place,
        update_default_file_types,
        update_content_inline_csp,
    )
    for component in config_wrapper:
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


def update_content_inline_csp(component: Component, request: Request) -> None:
    if component.get("type") == "content":
        """
        NOTE: we apply Bleach and a CSS declaration whitelist because content components are not purely "trusted" content from form-designers,
        but can contain malicious user input if the form designer uses variables inside the HTML
        (and the form submission data is passed as template context to those HTML blobs)
        """
        component["html"] = post_process_html(component["html"], request)
