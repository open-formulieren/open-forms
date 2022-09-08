from django.utils.translation import gettext_lazy as _

from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_basic_type,
    build_parameter_type,
)
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.utils import OpenApiParameter

from openforms.middleware import (
    CSRF_TOKEN_HEADER_NAME,
    IS_FORM_DESIGNER_HEADER_NAME,
    SESSION_EXPIRES_IN_HEADER,
)

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

# CSRF Token header
CSRF_TOKEN_PARAMETER = build_parameter_type(
    name=CSRF_TOKEN_HEADER_NAME,
    schema=build_basic_type(str),
    location=OpenApiParameter.HEADER,
    description=_("CSRF Token"),
    required=True,
)
del CSRF_TOKEN_PARAMETER["in"]
del CSRF_TOKEN_PARAMETER["name"]
CSRF_TOKEN_COMPONENT = ResolvedComponent(
    name=CSRF_TOKEN_HEADER_NAME,
    type="headers",
    schema=CSRF_TOKEN_PARAMETER,
    object=CSRF_TOKEN_HEADER_NAME,
)
# Can navigate between submission steps header
IS_FORM_DESIGNER_PARAMETER = build_parameter_type(
    name=IS_FORM_DESIGNER_HEADER_NAME,
    schema=build_basic_type(str),
    location=OpenApiParameter.HEADER,
    description=_(
        "If true, the user is allowed to navigate between submission steps even if previous submission steps have not"
        " been completed yet."
    ),
    required=True,
)
del IS_FORM_DESIGNER_PARAMETER["in"]
del IS_FORM_DESIGNER_PARAMETER["name"]
IS_FORM_DESIGNER_COMPONENT = ResolvedComponent(
    name=IS_FORM_DESIGNER_HEADER_NAME,
    type="headers",
    schema=IS_FORM_DESIGNER_PARAMETER,
    object=IS_FORM_DESIGNER_HEADER_NAME,
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
