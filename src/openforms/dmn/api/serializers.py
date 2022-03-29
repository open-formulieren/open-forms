from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.plugins.api.serializers import PluginBaseSerializer


class DecisionPluginSerializer(PluginBaseSerializer):
    pass


class DecisionDefinitionPlugin(serializers.Serializer):
    id = serializers.CharField(
        source="identifier",
        label=_("Identifier"),
        help_text=_(
            "The (unique) identifier pointing to a particular decision definition."
        ),
    )
    label = serializers.CharField(
        label=_("Label"),
        help_text=_("Human readable name/label identifying the decision definition"),
    )
