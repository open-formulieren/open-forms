from typing import assert_never

from drf_spectacular.authentication import SessionScheme
from drf_spectacular.extensions import (
    OpenApiSerializerExtension,
    OpenApiSerializerFieldExtension,
)
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import Direction


class AnonCSRFSessionScheme(SessionScheme):
    target_class = "openforms.api.authentication.AnonCSRFSessionAuthentication"
    # must be different name than the parent class, but it's effectively the same
    # behaviour
    name = "anonCSRFCookieAuth"


class ModelTranslationsSerializerExtension(OpenApiSerializerExtension):
    target_class = "openforms.translations.api.serializers.ModelTranslationsSerializer"
    match_subclasses = False

    def get_name(self) -> None | str:
        base = self.target.parent.__class__.__name__
        if base.endswith("Serializer"):
            base = base[:-10]
        return f"{base}{self.target_class.__name__}"

    def map_serializer(self, auto_schema: AutoSchema, direction):
        return auto_schema._map_serializer(
            self.target, direction, bypass_extensions=True
        )


class Base64ImageFieldExtensions(OpenApiSerializerFieldExtension):
    target_class = "openforms.api.fields.Base64ImageField"

    def map_serializer_field(
        self, auto_schema: AutoSchema, direction: Direction
    ) -> dict[str, object]:
        assert not self.target.allow_null
        assert self.target.use_url

        match direction:
            # XXX this branch is not hit because we don't enable COMPONENT_SPLIT_REQUEST,
            # and that change is too invasive for now
            case "request":
                schema = build_basic_type(OpenApiTypes.BYTE)
            case "response":
                schema = build_basic_type(OpenApiTypes.URI)
            case _:  # pragma: no cover
                assert_never(direction)

        assert schema is not None
        return schema
