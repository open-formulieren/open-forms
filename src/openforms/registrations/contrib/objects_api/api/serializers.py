from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class ObjecttypeSerializer(serializers.Serializer):
    # Keys are defined in camel case as this is what we get from the Objecttype API
    url = serializers.URLField(
        label=_(
            "URL reference to this object. This is the unique identification and location of this object."
        ),
    )
    uuid = serializers.UUIDField(label=_("Unique identifier (UUID4)."))
    name = serializers.CharField(label=_("Name of the object type."))
    namePlural = serializers.CharField(label=_("Plural name of the object type."))
    dataClassification = serializers.CharField(
        label=_("Confidential level of the object type.")
    )


class ObjecttypeVersionSerializer(serializers.Serializer):
    version = serializers.IntegerField(
        label=_("Integer version of the Objecttype."),
    )
    status = serializers.CharField(label=_("Status of the object type version"))


class TargetPathsSerializer(serializers.Serializer):
    target_path = serializers.ListField(
        child=serializers.CharField(label=_("Segment of a JSON path")),
        label=_("target path"),
        help_text=_(
            "Representation of the JSON target location as a list of string segments."
        ),
    )
    required = serializers.BooleanField(
        label=_("required"),
        help_text=_("Wether the path is marked as required in the JSON Schema."),
    )
    json_schema = serializers.DictField(
        label=_("json schema"),
        help_text=_("Corresponding (sub) JSON Schema of the target path."),
    )


class TargetPathsInputSerializer(serializers.Serializer):
    form_uuid = serializers.CharField(
        label=_("form_uuid"), help_text=_("UUID of the form")
    )
    backend_key = serializers.CharField(
        label=_("backend_key"), help_text=_("Key of the registration backend")
    )
    variable_key = serializers.CharField(
        label=_("variable_key"), help_text=_("Key of the variable")
    )
