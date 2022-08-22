from django.template import Context, Template
from django.urls import reverse

import elasticapm
from rest_framework.request import Request

from openforms.forms.custom_field_types import handle_custom_types
from openforms.prefill import inject_prefill
from openforms.submissions.models import Submission

from .normalization import normalize_value_for_component  # noqa
from .utils import format_date_value, iter_components, mimetype_allowed  # noqa


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
    configuration = insert_variables(configuration, submission=submission)
    return configuration


def insert_variables(configuration: dict, submission: Submission) -> dict:
    # TODO: refactor when interpolating configuration properties with variables
    inject_prefill(configuration, submission)

    value_variables_state = submission.load_submission_value_variables_state()
    data = value_variables_state.get_data()
    static_data = value_variables_state.static_data()

    for component in iter_components(configuration):
        if "html" in component:
            content_with_vars = Template(component.get("html", "")).render(
                Context({**data, **static_data})
            )
            component["html"] = content_with_vars

        # TODO: inject variables also in label

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
