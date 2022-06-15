from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.plugins.api.serializers import PluginBaseSerializer


class DecisionPluginSerializer(PluginBaseSerializer):
    pass


class DecisionDefinitionSerializer(serializers.Serializer):
    id = serializers.CharField(
        source="identifier",
        label=_("Identifier"),
        help_text=_(
            "The (unique) identifier pointing to a particular decision definition."
        ),
    )
    label = serializers.CharField(
        label=_("Label"),
        help_text=_("Human readable name/label identifying the decision definition."),
    )


class DecisionDefinitionVersionSerializer(serializers.Serializer):
    id = serializers.CharField(
        label=_("version identifier"),
        help_text=_(
            "The (unique) identifier pointing to a particular decision definition version."
        ),
    )
    label = serializers.CharField(
        label=_("Label"),
        help_text=_("Textual representation of the definition version."),
    )


class DecisionDefinitionXMLSerializer(serializers.Serializer):
    xml = serializers.CharField(
        label=_("DMN XML"),
        help_text=_("If no XML can be obtained, the value will be an empty string."),
    )
