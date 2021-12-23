from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin


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
    # TODO: derived_variables, variables_to_include (from component keys) - might have
    # to be done in react alltogether
