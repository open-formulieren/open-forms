from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.fields import SlugRelatedAsChoicesField
from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.utils.mixins import JsonSchemaSerializerMixin

from ..typing import ObjectsAPIOptions


class PrefillTargetPathsSerializer(serializers.Serializer):
    target_path = serializers.ListField(
        child=serializers.CharField(label=_("Segment of a JSON path")),
        label=_("target path"),
        help_text=_(
            "Representation of the JSON target location as a list of string segments."
        ),
    )
    json_schema = serializers.DictField(
        label=_("json schema"),
        help_text=_("Corresponding (sub) JSON Schema of the target path."),
    )


class ObjecttypeVariableMappingSerializer(serializers.Serializer):
    """
    A mapping between a form variable key and the corresponding Objecttype attribute.
    """

    variable_key = FormioVariableKeyField(
        label=_("variable key"),
        help_text=_(
            "The 'dotted' path to a form variable key. The format should comply to how "
            "Formio handles nested component keys."
        ),
    )
    target_path = serializers.ListField(
        child=serializers.CharField(label=_("Segment of a JSON path")),
        label=_("target path"),
        help_text=_(
            "Representation of the JSON target location as a list of string segments."
        ),
    )


class ObjectsAPIOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    objects_api_group = SlugRelatedAsChoicesField(
        queryset=ObjectsAPIGroupConfig.objects.exclude(
            Q(objects_service=None) | Q(objecttypes_service=None)
        ),
        slug_field="identifier",
        label=("Objects API group"),
        required=True,
        help_text=_("Which Objects API group to use."),
    )
    objecttype_uuid = serializers.UUIDField(
        label=_("objecttype"),
        required=True,
        help_text=_("UUID of the objecttype in the Objecttypes API. "),
    )
    objecttype_version = serializers.IntegerField(
        label=_("objecttype version"),
        required=True,
        help_text=_("Version of the objecttype in the Objecttypes API."),
    )
    skip_ownership_check = serializers.BooleanField(
        label=_("skip ownership check"),
        help_text=_(
            "If enabled, no authentication/ownership checks of the referenced object "
            "are performed."
        ),
        default=False,
    )
    auth_attribute_path = serializers.ListField(
        child=serializers.CharField(label=_("Segment of a JSON path")),
        label=_("Path to auth attribute (e.g. BSN/KVK) in objects"),
        help_text=_(
            "This is used to perform validation to verify that the authenticated "
            "user is the owner of the object."
        ),
        required=False,
        default=list,
        allow_empty=True,
    )
    variables_mapping = ObjecttypeVariableMappingSerializer(
        label=_("variables mapping"),
        many=True,
        required=True,
    )

    def validate(self, attrs: ObjectsAPIOptions) -> ObjectsAPIOptions:
        # ensure that an auth_attribute_path is specified when ownership checks are
        # not skipped.
        if not attrs["skip_ownership_check"] and not attrs["auth_attribute_path"]:
            raise serializers.ValidationError(
                {
                    "auth_attribute_path": _(
                        "You must specify which attribute to compare the authenticated "
                        "user identifier with."
                    ),
                },
                code="empty",
            )

        return attrs
