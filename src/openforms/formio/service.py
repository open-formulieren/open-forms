from django.template import Context, Template
from django.urls import reverse

import elasticapm
from rest_framework.request import Request

from openforms.formio.utils import iter_components
from openforms.forms.custom_field_types import handle_custom_types
from openforms.prefill import apply_prefill
from openforms.submissions.models import Submission


# TODO: it might be beneficial to memoize this function if it runs multiple times in
# the context of the same request
@elasticapm.capture_span(span_type="app.formio")
def get_dynamic_configuration(
    configuration: dict, request: Request, submission: Submission
) -> dict:
    """
    Given a static Formio configuration, apply the hooks to dynamically transform this.

    The configuration is modified in the context of the provided :arg:`submission`.
    """
    configuration = handle_custom_types(
        configuration, request=request, submission=submission
    )
    configuration = apply_prefill(configuration, submission=submission)
    configuration = insert_variables(configuration, submission=submission)
    return configuration


def update_configuration_for_request(configuration: dict, request: Request) -> dict:
    """
    Given a static Formio configuration, apply dynamic changes we always must do, like setting absolute urls.

    The configuration is modified in the context of the provided :arg:`submission`.
    """
    update_urls_in_place(configuration, request)


def update_urls_in_place(configuration: dict, request: Request):
    for component in iter_components(configuration):
        if component.get("type") == "file":
            component["url"] = request.build_absolute_uri(
                reverse("api:formio:temporary-file-upload")
            )


def insert_variables(configuration, submission):
    # TODO
    for component in iter_components(configuration):
        if component.get("type") == "content":
            content_with_vars = Template(component.get("html", "")).render(
                Context(submission.data)
            )
            component["html"] = content_with_vars

    return configuration
