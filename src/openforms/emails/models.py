from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.appointments.models import AppointmentInfo
from openforms.submissions.models import Submission

from .validators import DjangoTemplateValidator


class ConfirmationEmailTemplateManager(models.Manager):
    @staticmethod
    def set_for_form(form=None, data=None):
        if data and data.get("subject") and data.get("content"):
            try:
                # First try updating the current confirmation email template
                form.confirmation_email_template.subject = data["subject"]
                form.confirmation_email_template.content = data["content"]
                form.confirmation_email_template.save()
            except (AttributeError, ConfirmationEmailTemplate.DoesNotExist):
                # If one does not exist then create it
                ConfirmationEmailTemplate.objects.create(form=form, **data)
        else:
            try:
                # If a complete email template is not given then delete the potential confirmation email template
                #   This handles the case where a template was created but later cleared
                form.confirmation_email_template.delete()
            except (AttributeError, ConfirmationEmailTemplate.DoesNotExist):
                pass


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

    objects = ConfirmationEmailTemplateManager()

    class Meta:
        verbose_name = _("Confirmation email template")
        verbose_name_plural = _("Confirmation email templates")

    def __str__(self):
        return f"Confirmation email template - {self.form}"
