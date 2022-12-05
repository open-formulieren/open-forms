from drf_spectacular.authentication import SessionScheme
from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.openapi import AutoSchema


class AnonCSRFSessionScheme(SessionScheme):
    target_class = "openforms.api.authentication.AnonCSRFSessionAuthentication"


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
