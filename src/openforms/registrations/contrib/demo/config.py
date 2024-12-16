from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin


class DemoOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    extra_line = serializers.CharField(
        label=_("Extra print statement"),
        required=False,
        allow_blank=True,
    )
