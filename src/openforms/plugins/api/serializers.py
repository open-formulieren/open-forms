from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class PluginBaseSerializer(serializers.Serializer):
    id = serializers.CharField(
        source="identifier",
        label=_("ID"),
        help_text=_("The unique plugin identifier"),
    )
    label = serializers.CharField(
        source="verbose_name",
        label=_("Label"),
        help_text=_("The human-readable name for a plugin."),
    )
