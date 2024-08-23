"""
Track the state of email verification.

Formio email address components optionally require verification to be sure the email
account exists and the user has access to it. The actual verification process happens
during the form submission and the state is inspected during form submission validation.

See https://github.com/open-formulieren/open-forms/issues/4542.
"""

from django.conf import settings
from django.db import models
from django.utils import translation
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from openforms.config.models import GlobalConfiguration
from openforms.emails.utils import send_mail_html
from openforms.formio.validators import variable_key_validator
from openforms.template import render_from_string

from .submission import Submission


def generate_verification_code():
    """
    Generate a 6-character verification code.

    The code is not required to be globally unique, so it's okay if the same code is
    generated for different email addresses.
    """
    return get_random_string(length=6, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")


class EmailVerification(models.Model):
    """
    Hold the verification state for a single email address.

    An email verification is always bound to a specific submission *and* component key.
    Multiple emails may go through the verification process, either because the
    component supports multiple values or the user changed the entered email address.
    """

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        verbose_name=_("submission"),
        help_text=_(
            "The submission during which the email verification was initiated."
        ),
    )
    component_key = models.TextField(
        _("component key"),
        help_text=_("Key of the email component in the submission's form."),
        validators=[variable_key_validator],
    )
    email = models.EmailField(
        _("email address"),
        help_text=_("The email address that is being verified."),
    )
    verification_code = models.CharField(
        _("verification code"),
        max_length=6,
        default=generate_verification_code,
    )
    verified_on = models.DateTimeField(
        _("verification timestamp"),
        null=True,
        blank=True,
        help_text=_("Unverified emails have no timestamp set."),
    )

    class Meta:
        verbose_name = _("email verification")
        verbose_name_plural = _("email verifications")

    def __str__(self):
        return _("{email} (component '{component}'): {status}").format(
            email=self.email,
            component=self.component_key,
            status=_("verified") if self.verified_on else _("not verified"),
        )

    def send_email(self):
        """
        Send the verification email.
        """
        with translation.override(self.submission.language_code):
            config = GlobalConfiguration.get_solo()
            form_name = self.submission.form.name
            context = {
                "form_name": form_name,
                "code": self.verification_code,
            }

            subject = render_from_string(
                config.email_verification_request_subject, context
            )
            content = render_from_string(
                config.email_verification_request_content, context
            )

        send_mail_html(
            subject=subject,
            html_body=content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            theme=self.submission.form.theme,
        )
