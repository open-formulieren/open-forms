from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin

from .constants import AttachmentFormat


class EmailOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    to_emails = serializers.ListField(
        child=serializers.EmailField(),
        label=_("The email addresses to which the submission details will be sent"),
        required=True,
    )
    attachment_formats = serializers.ListField(
        child=serializers.ChoiceField(choices=AttachmentFormat),
        label=_("The format(s) of the attachment(s) containing the submission details"),
        required=False,
    )
