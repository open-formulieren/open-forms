from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.api_models.catalogi import Catalogus, InformatieObjectType
from zgw_consumers.drf.serializers import APIModelSerializer

from openforms.plugins.api.serializers import PluginBaseSerializer


class RegistrationPluginSerializer(PluginBaseSerializer):
    schema = serializers.DictField(
        source="configuration_options.display_as_jsonschema",
        label=_("JSON schema"),
        help_text=_("The generated JSON schema for the plugin options."),
    )


@dataclass
class ChoiceWrapper:
    choice: tuple

    def __post_init__(self):
        self.value = self.choice[0]
        self.label = self.choice[1]


class RegistrationAttributeSerializer(serializers.Serializer):
    id = serializers.CharField(
        source="value",
        label=_("ID"),
        help_text=_("The unique attribute identifier"),
    )
    label = serializers.CharField(
        label=_("Label"),
        help_text=_("The human-readable name for an attribute."),
    )


class InformatieObjectTypeSerializer(APIModelSerializer):
    class Meta:
        model = InformatieObjectType
        fields = (
            "url",
            "omschrijving",
        )


class CatalogusDomainSerializer(APIModelSerializer):
    class Meta:
        model = Catalogus
        fields = ("domein", "rsin")


class InformatieObjectTypeChoiceSerializer(serializers.Serializer):
    informatieobjecttype = InformatieObjectTypeSerializer()
    catalogus = CatalogusDomainSerializer()
