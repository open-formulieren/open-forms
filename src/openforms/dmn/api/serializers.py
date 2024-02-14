from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.plugins.api.serializers import PluginBaseSerializer

from .constants import DMNTypes


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


class DecisionDefinitionInputSerializer(serializers.Serializer):
    id = serializers.CharField(
        label=_("ID"), help_text=_("Unique identifier of the decision table input.")
    )
    label = serializers.CharField(
        label=_("label"), help_text=_("Short description of the input.")
    )
    expression = serializers.CharField(
        label=_("expression"),
        help_text=_(
            "Specifies how the value of the input clause is generated. "
            "It usually simple references a variable which is available during the evaluation."
        ),
    )
    type_ref = serializers.ChoiceField(
        choices=DMNTypes.choices,
        help_text=_("The type of the input expression after being evaluated."),
    )


class DecisionDefinitionOutputSerializer(serializers.Serializer):
    id = serializers.CharField(
        label=_("ID"), help_text=_("Unique identifier of the decision table output.")
    )
    label = serializers.CharField(
        label=_("label"), help_text=_("Short description of the output.")
    )
    name = serializers.CharField(
        label=_("name"),
        help_text=_("Used to reference the value of the output."),
    )
    type_ref = serializers.ChoiceField(
        choices=DMNTypes.choices,
        help_text=_("The type of the output clause."),
    )


class DecisionDefinitionIntrospectionResultSerializer(serializers.Serializer):
    inputs = DecisionDefinitionInputSerializer(many=True)
    outputs = DecisionDefinitionOutputSerializer(many=True)
