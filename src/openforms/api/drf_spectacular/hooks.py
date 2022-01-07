from django.utils.translation import gettext_lazy as _

from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_basic_type,
    build_parameter_type,
)
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.utils import OpenApiParameter

from openforms.middleware import SESSION_EXPIRES_IN_HEADER

SESSION_EXPIRES_IN_PARAMETER = build_parameter_type(
    name=SESSION_EXPIRES_IN_HEADER,
    schema=build_basic_type(str),
    location=OpenApiParameter.HEADER,
    description=_(
        "Amount of time in seconds after which the session expires. After this time "
        "has passed, the session is expired and the user is 'logged out'. Note "
        "that every subsequent API call resets the expiry."
    ),
    required=True,
)
# following drf_spectacular.openapi.AutoSchema._get_response_headers_for_code, this is
# not present in header objects
del SESSION_EXPIRES_IN_PARAMETER["in"]
del SESSION_EXPIRES_IN_PARAMETER["name"]

SESSION_EXPIRES_IN_COMPONENT = ResolvedComponent(
    name=SESSION_EXPIRES_IN_HEADER,
    # see https://swagger.io/specification/#components-object
    type="headers",  # TODO ResolvedComponent.HEADER does not exist yet -> PR upstream
    schema=SESSION_EXPIRES_IN_PARAMETER,
    object=SESSION_EXPIRES_IN_HEADER,
)


def add_middleware_headers(result, generator, request, public):
    """
    Schema generator hook to add headers to responses set by middleware.
    """
    generator.registry.register_on_missing(SESSION_EXPIRES_IN_COMPONENT)

    for path in result["paths"].values():
        for operation in path.values():
            # the paths object may be extended with custom, non-standard extensions
            if "responses" not in operation:  # pragma: no cover
                continue

            for response in operation["responses"].values():
                # spec: https://swagger.io/specification/#response-object
                response.setdefault("headers", {})
                response["headers"][
                    SESSION_EXPIRES_IN_HEADER
                ] = SESSION_EXPIRES_IN_COMPONENT.ref

    result["components"] = generator.registry.build(
        spectacular_settings.APPEND_COMPONENTS
    )

    return result
