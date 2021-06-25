from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class ValidationInputSerializer(serializers.Serializer):
    value = serializers.CharField(
        label=_("value"), help_text=_("Value to be validated")
    )


class ValidationResultSerializer(serializers.Serializer):
    is_valid = serializers.BooleanField(
        label=_("Is valid"), help_text=_("Boolean indicating value passed validation.")
    )
    messages = serializers.ListField(
        serializers.CharField(
            label=_("error message"),
            help_text=_("error message"),
        ),
        help_text=_("List of validation error messages for display."),
    )
