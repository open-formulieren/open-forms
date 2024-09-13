from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


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
