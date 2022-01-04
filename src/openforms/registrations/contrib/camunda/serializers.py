from django.utils.translation import gettext_lazy as _

from drf_polymorphic.serializers import PolymorphicSerializer
from rest_framework import serializers

from openforms.api.utils import get_from_serializer_data_or_instance
from openforms.utils.mixins import JsonSchemaSerializerMixin

from .constants import (
    JSONComplexVariableTypes,
    JSONVariableTypes,
    VariableSourceChoices,
)
from .fields import NullField


class MappedVariableSerializer(serializers.Serializer):
    enabled = serializers.BooleanField(
        label=_("enable"),
        help_text=_("Only enabled variables are passed into the process"),
    )
    # TODO: add validator to check that the component exists? we need the form context
    # for that though.
    component_key = serializers.CharField(
        label=_("Component key"),
        help_text=_("Key of the Formio.js component to take the value from."),
        required=True,
    )
    alias = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        label=_("Alias"),
        help_text=_(
            "If provided, the Camunda process variable will have this alias as name "
            "instead of the component key. Use this to map a component onto a different "
            "process variable name."
        ),
    )


class StringTypeDefinitionSerializer(serializers.Serializer):
    definition = serializers.CharField(
        label=_("Definition"),
        help_text=_("The string value for the variable"),
    )


class NumberTypeDefinitionSerializer(serializers.Serializer):
    definition = serializers.FloatField(
        label=_("Definition"),
        help_text=_("The number value for the variable"),
    )


class BooleanTypeDefinitionSerializer(serializers.Serializer):
    definition = serializers.BooleanField(
        label=_("Definition"),
        help_text=_("The boolean value for the variable"),
    )


class NullTypeDefinitionSerializer(serializers.Serializer):
    definition = NullField(
        label=_("Definition"),
        help_text=_("The value must always be 'null' for the 'null' type."),
    )


class ManualVariableSerializer(PolymorphicSerializer):
    type = serializers.ChoiceField(
        choices=JSONVariableTypes,
        required=True,
        allow_blank=False,
        label=_("Manual variable type"),
        help_text=_("Select the JSON variable type (manual source only)."),
    )

    discriminator_field = "type"
    serializer_mapping = {
        JSONVariableTypes.string: StringTypeDefinitionSerializer,
        JSONVariableTypes.number: NumberTypeDefinitionSerializer,
        JSONVariableTypes.boolean: BooleanTypeDefinitionSerializer,
        JSONVariableTypes.null: NullTypeDefinitionSerializer,
        JSONVariableTypes.object: "",
        JSONVariableTypes.array: "",
    }


class ComponentJSONLogicLookupSerializer(serializers.Serializer):
    # TODO: this can be replaced in the future with full-fledged JSON logic

    # TODO: add validator to check that the component exists? we need the form context
    # for that though. See also :class:`MappedVariableSerializer`
    var = serializers.CharField(
        label=_("Component key"),
        help_text=_("Key of the Formio.js component to take the value from."),
        required=True,
    )


class ComponentVariableSerializer(serializers.Serializer):
    definition = ComponentJSONLogicLookupSerializer()


class VariableDefinitionSerializer(PolymorphicSerializer):
    source = serializers.ChoiceField(
        choices=VariableSourceChoices,
        label=_("Variable source"),
        help_text=_("Designates where the value of the variable is sourced."),
    )

    discriminator_field = "source"
    serializer_mapping = {
        VariableSourceChoices.component: ComponentVariableSerializer,
        VariableSourceChoices.manual: ManualVariableSerializer,
    }


class ObjectVariableDefinitionSerializer(serializers.Serializer):
    definition = serializers.DictField(
        child=VariableDefinitionSerializer(),
        label=_("Definition"),
        help_text=_("The object with nested variable definitions"),
    )


class ArrayVariableDefinitionSerializer(serializers.Serializer):
    definition = serializers.ListField(
        child=VariableDefinitionSerializer(),
        label=_("Definition"),
        help_text=_("The list with nested variable definitions"),
    )


# recursive references, fun!
ManualVariableSerializer.serializer_mapping[
    JSONVariableTypes.object
] = ObjectVariableDefinitionSerializer
ManualVariableSerializer.serializer_mapping[
    JSONVariableTypes.array
] = ArrayVariableDefinitionSerializer


class ComplexVariableSerializer(PolymorphicSerializer):
    enabled = serializers.BooleanField(
        label=_("enable"),
        help_text=_("Only enabled variables are passed into the process"),
    )
    alias = serializers.CharField(
        required=True,
        allow_blank=False,
        label=_("Alias"),
        help_text=_(
            "Name of the variable in the Camunda process instance. For complex "
            "variables, the name must be supplied."
        ),
    )
    type = serializers.ChoiceField(
        choices=JSONComplexVariableTypes.choices,
        label=_("Type"),
        help_text=_("The type determines how to interpret the variable definition."),
    )

    discriminator_field = "type"
    serializer_mapping = {
        JSONComplexVariableTypes.object: ObjectVariableDefinitionSerializer,
        JSONComplexVariableTypes.array: ArrayVariableDefinitionSerializer,
    }


class CamundaOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    process_definition = serializers.CharField(
        required=True,
        help_text=_("The process definition for which to start a process instance."),
    )
    process_definition_version = serializers.IntegerField(
        required=False,
        help_text=_(
            "Which version of the process definition to start. The latest version is "
            "used if not specified."
        ),
        allow_null=True,
    )
    process_variables = MappedVariableSerializer(
        many=True,
        label=_("Mapped process variables"),
    )
    complex_process_variables = ComplexVariableSerializer(
        many=True,
        label=_("Complex process variables"),
    )

    def validate(self, attrs: dict) -> dict:
        # check for duplicated variable names
        mapped_variables = (
            get_from_serializer_data_or_instance(
                "process_variables", attrs, serializer=self
            )
            or []
        )
        complex_process_variables = (
            get_from_serializer_data_or_instance(
                "complex_process_variables", attrs, serializer=self
            )
            or []
        )

        var_names_seen = set()
        var_names_duplicated = []
        simple_var_names = [
            variable["alias"] or variable["component_key"]
            for variable in mapped_variables
        ]
        complex_var_names = [
            variable["alias"] for variable in complex_process_variables
        ]
        for var_name in simple_var_names + complex_var_names:
            if var_name in var_names_seen:
                var_names_duplicated.append(var_name)
            else:
                var_names_seen.add(var_name)

        if var_names_duplicated:
            raise serializers.ValidationError(
                _(
                    "The variable name(s) '{var_names}' occur(s) multiple times. Hint: check that "
                    "they are not specified in both the process variables and complex process variables."
                ).format(var_names=", ".join(set(var_names_duplicated))),
                code="duplicate-variables",
            )

        return attrs
