from typing import TypedDict

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.utils.mixins import JsonSchemaSerializerMixin


def validate_path(v: str) -> None:
    """Validate path by checking if it contains '..', which can lead to path traversal
    attacks.

    :param v: path to validate
    """
    if ".." in v:
        raise ValidationError(
            "Path cannot contain '..', as it can lead to path traversal attacks."
        )


class JSONDumpOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    service = PrimaryKeyRelatedAsChoicesField(
        queryset=Service.objects.filter(api_type=APITypes.orc),
        label=_("Service"),
        help_text=_("Which service to use."),
        required=True,
    )
    path = serializers.CharField(
        max_length=255,
        label=_("Path"),
        help_text=_("Path relative to the Service API root."),
        allow_blank=True,
        required=False,
        default="",
        validators=[validate_path],
    )
    variables = serializers.ListField(
        child=FormioVariableKeyField(),
        label=_("Variable key list"),
        help_text=_("A list of variables to use."),
        required=True,
        min_length=1,
    )
    fixed_metadata_variables = serializers.ListField(
        child=FormioVariableKeyField(),
        default=[
            "public_reference",
            "form_name",
            "form_version",
            "form_id",
            "registration_timestamp",
            "auth_type",
        ],
        label=_("Fixed metadata variable key list"),
        help_text=_(
            "A list of required variables to use in the metadata. These include "
            "the registration variables of the JSON dump plugin"
        ),
        required=False,
    )
    additional_metadata_variables = serializers.ListField(
        child=FormioVariableKeyField(),
        label=_("Additional metadata variable key list"),
        help_text=_("A list of additional variables to use in the metadata"),
        required=False,
        default=list,
    )


class JSONDumpOptions(TypedDict):
    """
    JSON dump registration plugin options

    This describes the shape of :attr:`JSONDumpOptionsSerializer.validated_data`, after
    the input data has been cleaned/validated.
    """

    service: Service
    path: str
    variables: list[str]
    fixed_metadata_variables: list[str]
    additional_metadata_variables: list[str]
