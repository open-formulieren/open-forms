from typing import Any, Dict, Optional

import elasticapm
from rest_framework.request import Request

from openforms.submissions.models import Submission

__all__ = ["register", "unregister", "handle_custom_types"]

REGISTRY = {}


def register(custom_type: str):
    def decorator(handler: callable):
        if custom_type in REGISTRY:
            raise ValueError(f"Custom type {custom_type} is already registered.")

        REGISTRY[custom_type] = handler

    return decorator


def unregister(custom_type: str):
    if custom_type in REGISTRY:
        del REGISTRY[custom_type]


def find_nested_component_key(component) -> Optional[str]:
    # keys_to_try = ["columns", "components"]
    keys_to_try = ["components"]
    for key in keys_to_try:
        has_children = bool(component.get(key))
        if has_children:
            return key

    return None


@elasticapm.capture_span(span_type="app.formio")
def handle_custom_types(
    configuration: Dict[str, Any],
    request: Request,
    submission: Submission,
) -> Dict[str, Any]:

    rewritten_components = []

    for component in configuration["components"]:
        type_key = component["type"]

        # no handler -> leave untouched
        if type_key not in REGISTRY:
            rewritten_component = component
        # if there is a handler, invoke it
        else:
            handler = REGISTRY[type_key]
            rewritten_component = handler(component, request, submission)

        # recurse to handle nested components
        # TODO: does not handle columns at all yet!
        nested_component_key = find_nested_component_key(rewritten_component)
        if nested_component_key:
            rewritten_component.update(
                handle_custom_types(
                    rewritten_component, request=request, submission=submission
                )
            )

        rewritten_components.append(rewritten_component)

    return {
        "components": rewritten_components,
    }
