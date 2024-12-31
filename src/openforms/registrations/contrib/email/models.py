from functools import partial

from django.db import models
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from tinymce.models import HTMLField

from openforms.emails.validators import URLSanitationValidator
from openforms.template.validators import DjangoTemplateValidator
from openforms.translations.utils import ensure_default_language

from .config import Options


@ensure_default_language()
def render_with_language(filename):
    return render_to_string(filename).strip()


get_subject = partial(
    render_with_language, "registrations/contrib/email/email_registration_subject.txt"
)
get_subject_payment = partial(
    render_with_language,
    "registrations/contrib/email/email_registration_subject_payment.txt",
)
get_content_html = partial(
    render_with_language, "registrations/contrib/email/email_registration_content.html"
)
get_content_text = partial(
    render_with_language, "registrations/contrib/email/email_registration_content.txt"
)


class EmailConfig(SingletonModel):
    """
    Global configuration and defaults for the email registration backend.
    """

    attach_files_to_email = models.BooleanField(
        _("attach files to email"),
        default=False,
        help_text=_(
            "Enable to attach file uploads to the registration email. Note that this "
            "is the global default which may be overridden per form. Form designers "
            "should take special care to ensure that the total file upload sizes do "
            "not exceed the email size limit."
        ),
    )
    subject = models.CharField(
        _("subject"),
        max_length=1000,
        help_text=_(
            "Subject of the registration email message. Can be overridden on the form level."
        ),
        default=get_subject,
        validators=[DjangoTemplateValidator()],
    )
    payment_subject = models.CharField(
        _("payment subject"),
        max_length=1000,
        help_text=_(
            "Subject of the registration email message that is sent when the payment is received. Can be overridden on the form level."
        ),
        default=get_subject_payment,
        validators=[DjangoTemplateValidator()],
    )
    content_html = HTMLField(
        _("content HTML"),
        help_text=_(
            "Content of the registration email message (as HTML). Can be overridden on the form level."
        ),
        default=get_content_html,
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
            URLSanitationValidator(),
        ],
    )
    content_text = models.TextField(
        _("content text"),
        help_text=_(
            "Content of the registration email message (as text). Can be overridden on the form level."
        ),
        default=get_content_text,
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
            URLSanitationValidator(),
        ],
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        verbose_name = _("Email registration configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)

    def apply_defaults_to(self, options: Options):
        # key may be present and have the value None, or may be absent -> .get also returns None
        current_val = options.get("attach_files_to_email")
        if current_val is None:
            options["attach_files_to_email"] = self.attach_files_to_email
