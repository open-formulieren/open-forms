"""
Non-API related serializers, typically used to validate data-structures in ``JSONField``
type model fields.
"""

from drf_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers

# import from `constants` to avoid circ. import:
from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import register


class PluginMixin:
    def get_fields(self):
        fields = super().get_fields()  # type: ignore
        fields["plugin"].choices = register.get_choices()
        return fields


class CoSignV1DataSerializer(PluginMixin, serializers.Serializer):
    plugin = serializers.ChoiceField(choices=())
    identifier = serializers.CharField()
    representation = serializers.CharField(required=False, allow_blank=True, default="")
    co_sign_auth_attribute = serializers.ChoiceField(choices=AuthAttribute.choices)
    # TODO: validate fields shape depending on value of plugin (polymorphic serializer)
    fields = serializers.DictField(  # type: ignore
        child=serializers.CharField(allow_blank=True),
        required=False,
        allow_null=True,
    )


class CoSignV2DataSerializer(PluginMixin, serializers.Serializer):
    plugin = serializers.ChoiceField(choices=())
    attribute = serializers.ChoiceField(choices=AuthAttribute.choices)
    value = serializers.CharField()
    cosign_date = serializers.DateTimeField()


class CoSignDataSerializer(PolymorphicSerializer):
    version = serializers.ChoiceField(choices=("v1", "v2"))

    discriminator_field = "version"
    serializer_mapping = {
        "v1": CoSignV1DataSerializer,
        "v2": CoSignV2DataSerializer,
    }

    # TODO: fixup in the upstream library!
    def _get_serializer_from_data(self, data):
        try:
            return super()._get_serializer_from_data(data)
        except KeyError:
            return serializers.Serializer(data={})
