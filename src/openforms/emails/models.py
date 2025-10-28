from __future__ import annotations

from typing import ClassVar

from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.emails.validators import URLSanitationValidator
from openforms.forms.models import Form
from openforms.template.validators import DjangoTemplateValidator


class ConfirmationEmailTemplateManager(models.Manager["ConfirmationEmailTemplate"]):
    def set_for_form(self, form: Form, data: dict | None):
        # if there's *no* template data, make sure that we do indeed wipe the fields,
        # making the template not usable
        if not data:
            data = {
                "subject": "",
                "content": "",
                "cosign_subject": "",
                "cosign_content": "",
            }

        return self.update_or_create(form=form, defaults=data)


class ConfirmationEmailTemplate(models.Model):
    """Template of email to be sent on completion of submission"""

    subject = models.CharField(
        _("subject"),
        blank=True,
        max_length=1000,
        help_text=_("Subject of the email message"),
        validators=[DjangoTemplateValidator()],
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
                ],
                backend="openforms.template.openforms_backend",
            ),
            URLSanitationValidator(),
        ],
    )
    cosign_subject = models.CharField(
        _("cosign subject"),
        blank=True,
        max_length=1000,
        help_text=_("Subject of the email message when the form requires cosigning."),
        validators=[DjangoTemplateValidator()],
    )
    cosign_content = models.TextField(
        _("cosign content"),
        blank=True,
        help_text=_(
            "The content of the email message when cosgining is required. You must "
            "include the '{% payment_information %}' and '{% cosign_information %}' "
            "instructions. Additionally, you can use the '{% confirmation_summary %}' "
            "instruction and some additional variables - see the documentation for "
            "details."
        ),
        validators=[
            DjangoTemplateValidator(
                required_template_tags=[
                    "payment_information",
                    "cosign_information",
                ],
                backend="openforms.template.openforms_backend",
            ),
            URLSanitationValidator(),
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

    objects: ClassVar[  # pyright: ignore[reportIncompatibleVariableOverride]
        ConfirmationEmailTemplateManager
    ] = ConfirmationEmailTemplateManager()

    form_id: int | None

    class Meta:
        verbose_name = _("Confirmation email template")
        verbose_name_plural = _("Confirmation email templates")

    def __str__(self):
        form_str = str(self.form) if self.form_id else _("(unsaved form)")
        return _("Confirmation email template - {form}").format(form=form_str)
