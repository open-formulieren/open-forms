from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.plugins.api.serializers import PluginBaseSerializer


class RegistrationPluginSerializer(PluginBaseSerializer):
    schema = serializers.JSONField(
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


@dataclass
class InformatieObjectTypeWrapper:
    iotype: tuple

    def __post_init__(self):
        self.description = self.iotype[0]
        self.url = self.iotype[1]
        self.catalogus_domain = self.iotype[2]


class InformatieObjectTypeSerializer(serializers.Serializer):
    description = serializers.CharField(
        label=_("omschrijving"),
        help_text=_("The description of the InformatieObjectType"),
    )
    url = serializers.URLField(
        label=_("url"),
        help_text=_("The URL of the InformatieObjectType."),
    )
    catalogus_domain = serializers.CharField(
        label=_("catalogus domein"),
        help_text=_("The domain of the related Catalogus"),
    )
