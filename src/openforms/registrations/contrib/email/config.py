from typing import NotRequired, TypedDict

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.validators import AllOrNoneTruthyFieldsValidator
from openforms.emails.validators import URLSanitationValidator
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.mixins import JsonSchemaSerializerMixin

from .constants import AttachmentFormat


class Options(TypedDict):
    """
    Shape of the email registration plugin options.

    This describes the shape of :attr:`EmailOptionsSerializer.validated_data`, after
    the input data has been cleaned/validated.
    """

    to_emails: list[str]
    to_emails_from_variable: NotRequired[str]
    attachment_formats: NotRequired[list[AttachmentFormat | str]]
    payment_emails: NotRequired[list[str]]
    attach_files_to_email: bool | None
    email_subject: NotRequired[str]
    email_payment_subject: NotRequired[str]
    email_content_template_html: NotRequired[str]
    email_content_template_text: NotRequired[str]


class EmailOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    to_emails = serializers.ListField(
        child=serializers.EmailField(),
        label=_("The email addresses to which the submission details will be sent"),
        # always required, even if using to_emails_from_variable because that may contain
        # bad data/unexpectedly be empty due to reasons (failing prefill, for example)
        required=True,
    )
    to_emails_from_variable = FormioVariableKeyField(
        label=_("Key of the target variable containing the email address"),
        required=False,
        allow_blank=True,
        help_text=_(
            "Key of the target variable whose value will be used for the mailing. "
            "When using this field, the mailing will only be sent to this email address. "
            "The email addresses field would then be ignored. "
        ),
    )
    attachment_formats = serializers.ListField(
        child=serializers.ChoiceField(choices=AttachmentFormat.choices),
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
            "Enable to attach file uploads to the registration email. If set, this "
            "overrides the global default. Form designers should take special care to "
            "ensure that the total file upload sizes do not exceed the email size limit."
        ),
    )
    email_subject = serializers.CharField(
        label=_("email subject"),
        help_text=_(
            "Subject of the email sent to the registration backend. You can use the expressions "
            "'{{ form_name }}' and '{{ public_reference }}' to include the form name and the reference "
            "number to the submission in the subject."
        ),
        required=False,
        allow_blank=True,
        validators=[
            DjangoTemplateValidator(backend="openforms.template.openforms_backend")
        ],
    )
    email_payment_subject = serializers.CharField(
        label=_("email payment subject"),
        help_text=_(
            "Subject of the email sent to the registration backend to notify a change in the payment status."
        ),
        required=False,
        allow_blank=True,
        validators=[
            DjangoTemplateValidator(backend="openforms.template.openforms_backend")
        ],
    )
    email_content_template_html = serializers.CharField(
        label=_("email content template HTML"),
        help_text=_("Content of the registration email message (as text)."),
        required=False,
        allow_blank=True,
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
            URLSanitationValidator(),
        ],
    )
    email_content_template_text = serializers.CharField(
        label=_("email content template text"),
        help_text=_("Content of the registration email message (as text)."),
        required=False,
        allow_blank=True,
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
            URLSanitationValidator(),
        ],
    )

    class Meta:
        validators = [
            AllOrNoneTruthyFieldsValidator(
                "email_content_template_html",
                "email_content_template_text",
            ),
        ]


# sanity check for development - keep serializer and type definitions in sync
_serializer_fields = EmailOptionsSerializer._declared_fields.keys()
_options_keys = Options.__annotations__.keys()
assert _serializer_fields == _options_keys, (
    "Mismatch between serializer fields and options dictionary keys!"
)
del _serializer_fields, _options_keys
