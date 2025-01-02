from typing import Required, TypedDict

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.utils.mixins import JsonSchemaSerializerMixin


class JSONDumpOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    service = PrimaryKeyRelatedAsChoicesField(
        queryset=Service.objects.filter(api_type=APITypes.orc),
        label=_("Service"),
        help_text=_("Which service to use."),
        required=True,
    )
    # TODO-4908: show the complete API endpoint as a (tooltip) hint after user entry?
    #  Might be a front-end thing...
    relative_api_endpoint = serializers.CharField(
        max_length=255,
        label=_("Relative API endpoint"),
        help_text=_(
            "The API endpoint to send the data to (relative to the service API root)."
        ),
        allow_blank=True,
        required=False,
        default="",
    )
    form_variables = serializers.ListField(
        child=FormioVariableKeyField(),
        label=_("Form variable key list"),
        help_text=_(
            "A list of form variables (can also include static variables) to use."
        ),
        required=True,
        min_length=1,
    )


class JSONDumpOptions(TypedDict):
    """
    JSON dump registration plugin options

    This describes the shape of :attr:`JSONDumpOptionsSerializer.validated_data`, after
    the input data has been cleaned/validated.
    """

    service: Service
    relative_api_endpoint: str
    form_variables: list[str]
