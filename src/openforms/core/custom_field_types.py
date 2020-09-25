from typing import Any, Dict

from rest_framework.request import Request

__all__ = ["register", "handle_custom_types"]

REGISTRY = {}


def register(custom_type: str):
    def decorator(handler: callable):
        if custom_type in REGISTRY:
            raise ValueError(f"Custom type {custom_type} is already registered.")

        REGISTRY[custom_type] = handler

    return decorator


def handle_custom_types(
    configuration: Dict[str, Any],
    request: Request,
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
        rewritten_components.append(handler(component, request))

    return {
        "components": rewritten_components,
    }
