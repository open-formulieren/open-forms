from rest_framework.request import Request

from openforms.forms.custom_field_types import handle_custom_types
from openforms.prefill import apply_prefill
from openforms.submissions.models import Submission


# TODO: it might be beneficial to memoize this function if it runs multiple times in
# the context of the same request
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
    configuration = apply_prefill(request, configuration, submission=submission)
    return configuration
