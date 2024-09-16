from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.contrib.objects_api.api.serializers import ObjectsAPIGroupInputSerializer


class TargetPathsSerializer(serializers.Serializer):
    target_path = serializers.ListField(
        child=serializers.CharField(label=_("Segment of a JSON path")),
        label=_("target path"),
        help_text=_(
            "Representation of the JSON target location as a list of string segments."
        ),
    )
    is_required = serializers.BooleanField(
        label=_("required"),
        help_text=_("Wether the path is marked as required in the JSON Schema."),
    )
    json_schema = serializers.DictField(
        label=_("json schema"),
        help_text=_("Corresponding (sub) JSON Schema of the target path."),
    )


class TargetPathsInputSerializer(ObjectsAPIGroupInputSerializer):
    objecttype = serializers.UUIDField(
        label=_("objecttype uuid"), help_text=("The UUID of the objecttype.")
    )
    objecttype_version = serializers.IntegerField(
        label=_("objecttype version"), help_text=_("The version of the objecttype.")
    )
    variable_json_schema = serializers.DictField(
        label=_("variable json schema"),
        help_text=_("The JSON Schema of the form variable."),
    )
