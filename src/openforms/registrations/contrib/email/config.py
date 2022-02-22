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
    payment_emails = serializers.ListField(
        child=serializers.EmailField(),
        label=_(
            "The email addresses to which the payment status update will be sent "
            "(defaults to general registration addresses)"
        ),
        required=False,
    )
    attach_files_to_email = serializers.BooleanField(
        label=_("attach files to email"),
        allow_null=True,
        default=None,  # falls back to the global default
        help_text=_(
            "Enable to attach file uploads to the registration email. Note that this "
            "is the global default which may be overridden per form. Form designers "
            "should take special care to ensure that the total file upload sizes do "
            "not exceed the email size limit."
        ),
    )
