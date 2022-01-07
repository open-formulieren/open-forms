from typing import Any, Dict

from rest_framework.request import Request

from openforms.forms.custom_field_types import handle_custom_types
from openforms.prefill import apply_prefill
from openforms.submissions.models import Submission


def iter_components(configuration: dict, recursive=True) -> dict:
    components = configuration.get("components")
    if configuration.get("type") == "columns" and recursive:
        assert not components, "Both nested components and columns found"
        for column in configuration["columns"]:
            yield from iter_components(configuration=column, recursive=recursive)

    if components:
        for component in components:
            yield component
            if recursive:
                yield from iter_components(configuration=component, recursive=recursive)


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
    configuration = apply_prefill(configuration, submission=submission)
    return configuration


def get_default_values(submission: Submission, configuration: dict) -> Dict[str, Any]:
    defaults = {}

    for component in iter_components(configuration, recursive=True):
        if "key" not in component:
            continue
        if "defaultValue" not in component:
            continue
        defaults[component["key"]] = component["defaultValue"]

    return defaults
