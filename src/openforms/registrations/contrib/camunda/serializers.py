from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin


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
        label=_("Alias"),
        help_text=_(
            "If provided, the Camunda process variable will have this alias as name "
            "instead of the component key. Use this to map a component onto a different "
            "process variable name."
        ),
    )


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
    # TODO: derived_variables, variables_to_include (from component keys) - might have
    # to be done in react alltogether
