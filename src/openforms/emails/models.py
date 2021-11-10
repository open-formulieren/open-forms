from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.appointments.models import AppointmentInfo
from openforms.submissions.models import Submission

from .utils import render_confirmation_email_content
from .validators import DjangoTemplateValidator


class ConfirmationEmailTemplate(models.Model):
    subject = models.CharField(
        _("subject"), max_length=1000, help_text=_("Subject of the email message")
    )
    content = models.TextField(
        _("content"),
        help_text=_(
            "The content of the email message can contain variables that will be "
            "templated from the submitted form data."
        ),
        validators=[
            DjangoTemplateValidator(
                required_template_tags=[
                    "appointment_information",
                    "payment_information",
                ]
            )
        ],
    )
    form = models.OneToOneField(
        "forms.Form",
        verbose_name=_("form"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="confirmation_email_template",
        help_text=_("The form for which this confirmation email template will be used"),
    )

    class Meta:
        verbose_name = _("Confirmation email template")
        verbose_name_plural = _("Confirmation email templates")

    def __str__(self):
        return f"Confirmation email template - {self.form}"

    def render(self, submission: Submission, extra_context=None):
        return render_confirmation_email_content(
            submission, self.content, extra_context=extra_context
        )
