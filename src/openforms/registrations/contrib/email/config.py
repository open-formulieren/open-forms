from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.jsonschema.mixins import JsonSchemaSerializerMixin


class EmailOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    to_emails = serializers.ListField(
        child=serializers.EmailField(),
        label=_("The email addresses to which the submission details will be sent"),
        required=True,
    )
