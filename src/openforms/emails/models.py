from typing import Optional

from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.forms.models import Form

from .validators import DjangoTemplateValidator


class ConfirmationEmailTemplateManager(models.Manager):
    def set_for_form(self, form: Form, data: Optional[dict]):
        # if there's *no* template data, make sure that we do indeed wipe the fields,
        # making the template not usable
        if not data:
            data = {"subject": "", "content": ""}

        return self.update_or_create(form=form, defaults=data)


class ConfirmationEmailTemplate(models.Model):
    subject = models.CharField(
        _("subject"),
        blank=True,
        max_length=1000,
        help_text=_("Subject of the email message"),
    )
    content = models.TextField(
        _("content"),
        blank=True,
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
        form_str = str(self.form) if self.form_id else _("(unsaved form)")
        return _("Confirmation email template - {form}").format(form=form_str)

    @property
    def is_usable(self) -> bool:
        return bool(self.subject and self.content)
