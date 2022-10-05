from django.utils.translation import gettext_lazy as _

from drf_spectacular.plumbing import build_parameter_type
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.utils import OpenApiParameter

from openforms.middleware import (
    CSRF_TOKEN_HEADER_NAME,
    IS_FORM_DESIGNER_HEADER_NAME,
    SESSION_EXPIRES_IN_HEADER,
)

from .plumbing import build_response_header_component

# Session Expires header
SESSION_EXPIRES_IN_COMPONENT = build_response_header_component(
    name=SESSION_EXPIRES_IN_HEADER,
    description=_(
        "Amount of time in seconds after which the session expires. After this time "
        "has passed, the session is expired and the user is 'logged out'. Note "
        "that every subsequent API call resets the expiry."
    ),
)

# CSRF Token header
CSRF_TOKEN_COMPONENT = build_response_header_component(
    name=CSRF_TOKEN_HEADER_NAME, description=_("CSRF Token")
)

# Is Form Designer header
IS_FORM_DESIGNER_COMPONENT = build_response_header_component(
    name=IS_FORM_DESIGNER_HEADER_NAME,
    description=_(
        "If true, the user is allowed to navigate between submission steps even if "
        "previous submission steps have not been completed yet."
    ),
)


def add_middleware_headers(result, generator, request, public):
    """
    Schema generator hook to add headers to responses set by middleware.
    """
    generator.registry.register_on_missing(SESSION_EXPIRES_IN_COMPONENT)
    generator.registry.register_on_missing(CSRF_TOKEN_COMPONENT)
    generator.registry.register_on_missing(IS_FORM_DESIGNER_COMPONENT)

    for path in result["paths"].values():
        for operation in path.values():
            # the paths object may be extended with custom, non-standard extensions
            if "responses" not in operation:  # pragma: no cover
                continue

            for response in operation["responses"].values():
                # spec: https://swagger.io/specification/#response-object
                response.setdefault("headers", {})
                response["headers"].update(
                    {
                        SESSION_EXPIRES_IN_HEADER: SESSION_EXPIRES_IN_COMPONENT.ref,
                        CSRF_TOKEN_HEADER_NAME: CSRF_TOKEN_COMPONENT.ref,
                        IS_FORM_DESIGNER_HEADER_NAME: IS_FORM_DESIGNER_COMPONENT.ref,
                    }
                )

    result["components"] = generator.registry.build(
        spectacular_settings.APPEND_COMPONENTS
    )

    return result


CSRF_TOKEN_PARAMETER = build_parameter_type(
    name=CSRF_TOKEN_HEADER_NAME,
    schema={"type": "string"},
    location=OpenApiParameter.HEADER,
    required=True,
)


def add_unsafe_methods_parameter(result, generator, request, public):
    """
    Schema generator hook to add parameters to endpoint with unsafe methods.
    """
    for path in result["paths"].values():
        for operation_method, operation in path.items():
            if operation_method not in ["post", "put", "patch", "delete"]:
                continue

            if "security" not in operation:
                continue

            for item in operation["security"]:
                if "cookieAuth" in item:
                    break
            else:
                continue

            if "parameters" not in operation:
                operation["parameters"] = []
            operation["parameters"].append(CSRF_TOKEN_PARAMETER)

    return result
