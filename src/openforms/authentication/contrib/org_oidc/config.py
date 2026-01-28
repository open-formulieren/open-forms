from typing import TypedDict

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin


class OIDCOptions(TypedDict):
    visible: bool


class OIDCOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    visible = serializers.BooleanField(
        label=_("visible"),
        default=True,
        help_text=_("Is the plugin always visible in the start of the form"),
    )
