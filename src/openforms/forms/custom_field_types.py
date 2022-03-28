from typing import Any, Dict, Optional

import elasticapm
from rest_framework.request import Request

from openforms.submissions.models import Submission, SubmissionStep

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


@elasticapm.capture_span(span_type="app.formio")
def handle_custom_types(
    configuration: Dict[str, Any],
    request: Request,
    submission: Submission,
    step: Optional[SubmissionStep] = None,
) -> Dict[str, Any]:

    rewritten_components = []

    for component in configuration["components"]:
        type_key = component["type"]

        # no handler -> leave untouched
        if type_key not in REGISTRY:
            rewritten_components.append(component)
            continue

        # if there is a handler, invoke it
        handler = REGISTRY[type_key]
        rewritten_components.append(handler(component, request, submission, step))

    return {
        "components": rewritten_components,
    }
