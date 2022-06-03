from django.db.models import Q
from django.template import Context, Template
from django.urls import reverse

import elasticapm
from rest_framework.request import Request

from openforms.config.models import GlobalConfiguration
from openforms.formio.utils import format_date_value, iter_components
from openforms.forms.custom_field_types import handle_custom_types
from openforms.prefill import _set_default_values, apply_prefill
from openforms.submissions.models import Submission, SubmissionValueVariable


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

    conf = GlobalConfiguration.get_solo()

    if conf.enable_form_variables:
        configuration = insert_variables(configuration, submission=submission)
    else:
        configuration = apply_prefill(configuration, submission=submission)

    return configuration


def insert_variables(configuration: dict, submission: Submission) -> dict:
    prefill_data = dict(
        SubmissionValueVariable.objects.filter(
            ~Q(form_variable__prefill_plugin=""), submission=submission
        ).values_list("key", "value")
    )

    value_variables_state = submission.load_submission_value_variables_state()
    data = value_variables_state.get_data()

    # TODO Once the enable_form_variables feature flag is removed, whe should move this code around
    _set_default_values(configuration, prefill_data)

    for component in iter_components(configuration):
        if "html" in component:
            content_with_vars = Template(component.get("html", "")).render(
                Context(data)
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
