from drf_spectacular.authentication import SessionScheme
from drf_spectacular.extensions import (
    OpenApiSerializerExtension,
    OpenApiSerializerFieldExtension,
)
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.settings import spectacular_settings
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
        assert self.target.use_url

        if not spectacular_settings.COMPONENT_SPLIT_REQUEST:
            # we have to cover for all possible types due to request/response being
            # different... not ideal
            schema = {
                "oneOf": [
                    build_basic_type(OpenApiTypes.URI),  # response
                    build_basic_type(OpenApiTypes.BYTE),  # request (base64 data)
                ],
                # DRF outputs null for empty file fields
                "nullable": self.target.allow_empty_file,
            }
        # currently we don't split request/response so this will never hit...
        else:  # pragma: no cover
            # request -> OpenApiTypes.BYTE or null, depending on allow_null
            # response -> OpenApiTypes.URI or null (irrespective of allow_null)
            raise NotImplementedError(
                "request/response separation is not implemented yet"
            )

        assert schema is not None
        return schema
