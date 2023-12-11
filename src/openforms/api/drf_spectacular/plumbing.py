from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_basic_type,
    build_parameter_type,
)
from drf_spectacular.utils import OpenApiParameter


def build_response_header_parameter(
    name: str,
    description: str,
    schema_type: type = str,
    required: bool = True,
    **kwargs,
):
    parameter = build_parameter_type(
        name=name,
        schema=build_basic_type(schema_type),
        location=OpenApiParameter.HEADER,
        description=description,
        required=required,
        **kwargs,
    )

    # following drf_spectacular.openapi.AutoSchema._get_response_headers_for_code, this is
    # not present in header objects
    del parameter["in"]
    del parameter["name"]

    return parameter


def build_response_header_component(
    name: str,
    description: str,
    schema_type: type = str,
    required: bool = True,
    **kwargs,
) -> ResolvedComponent:
    parameter = build_response_header_parameter(
        name=name,
        description=description,
        schema_type=schema_type,
        required=required,
        **kwargs,
    )
    component = ResolvedComponent(
        name=name,
        # see https://swagger.io/specification/#components-object
        # See upstream issue: https://github.com/tfranzel/drf-spectacular/issues/1128
        type="headers",
        schema=parameter,
        object=name,
    )
    return component
