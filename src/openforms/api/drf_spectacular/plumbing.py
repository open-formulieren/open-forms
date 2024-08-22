from typing import Any

from drf_spectacular.plumbing import (
    ResolvedComponent,
    build_basic_type,
    build_parameter_type,
    get_lib_doc_excludes as _get_lib_doc_excludes,
)
from drf_spectacular.utils import OpenApiParameter, inline_serializer
from rest_framework.fields import Field
from rest_framework.serializers import Serializer


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


def extend_inline_serializer(
    serializer: type[Serializer],
    fields: dict[str, Field],
    name: str = "",
    **kwargs: Any,
) -> Serializer:
    """Return an inline serializer, with fields extended from the provided serializer.

    If one of the provided extra fields already exists on the base serializer, it will be overridden.
    """
    return inline_serializer(
        name or serializer.__name__, serializer().get_fields() | fields, **kwargs
    )


def get_lib_doc_excludes():
    from openforms.contrib.zgw.api.serializers import CatalogueSerializer

    base = _get_lib_doc_excludes()
    extra = [
        CatalogueSerializer,
    ]
    return [*base, *extra]
