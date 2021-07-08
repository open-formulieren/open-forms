from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.plugins.api.serializers import PluginBaseSerializer


class PrefillPluginSerializer(PluginBaseSerializer):
    requires_auth = serializers.CharField(
        label=_("Required authentication attribute"),
        help_text=_(
            "The authentication attribute required for this plugin to lookup remote data."
        ),
        allow_null=True,
    )


@dataclass
class ChoiceWrapper:
    choice: tuple

    def __post_init__(self):
        self.value = self.choice[0]
        self.label = self.choice[1]


class AttributeSerializer(serializers.Serializer):
    id = serializers.CharField(
        source="value",
        label=_("ID"),
        help_text=_("The unique attribute identifier"),
    )
    label = serializers.CharField(
        label=_("Label"),
        help_text=_("The human-readable name for an attribute."),
    )
