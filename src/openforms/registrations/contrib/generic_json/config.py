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


class GenericJSONOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
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
    # Note: the defaults for this field are listed in `FixedMetadataVariableSerializer`.
    # They are in a separate API to make them available in the frontend as default fixed
    # options.
    # TODO: this list should be validated against the available FormVariable records
    #  that exist for the form.
    fixed_metadata_variables = serializers.ListField(
        child=FormioVariableKeyField(),
        label=_("Fixed metadata variable key list"),
        help_text=_(
            "A list of required variables to use in the metadata. These include "
            "the registration variables of the Generic JSON registration."
        ),
        required=True,
    )
    # TODO: this list should be validated against the available FormVariable records
    #  that exist for the form.
    additional_metadata_variables = serializers.ListField(
        child=FormioVariableKeyField(),
        label=_("Additional metadata variable key list"),
        help_text=_("A list of additional variables to use in the metadata."),
        required=False,
        default=list,
    )
    transform_to_list = serializers.ListField(
        child=FormioVariableKeyField(),
        label=_("Transform to list"),
        required=False,
        default=list,
        help_text=_(
            "Component keys in this list will be sent as an array of values rather than "
            "the default object-shape for selectboxes components."
        ),
    )
