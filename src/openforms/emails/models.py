from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context, Template, TemplateSyntaxError
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from openforms.appointments.models import AppointmentInfo
from openforms.submissions.models import Submission

from .utils import sanitize_content


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

    @staticmethod
    def get_context_data(submission: Submission) -> Dict[str, Any]:
        context = {
            # use private variables that can't be accessed in the template data, so that
            # template designers can't call the .delete method, for example. Variables
            # starting with underscores are blocked by the Django template engine.
            "_submission": submission,
            "_form": submission.form,  # should be the same as self.form
            **submission.data,
            "public_reference": submission.public_registration_reference,
        }

        try:
            context["_appointment_id"] = submission.appointment_info.appointment_id
        except AppointmentInfo.DoesNotExist:
            pass

        return context

    def render(self, submission: Submission):
        context = self.get_context_data(submission)

        # render the e-mail body - the template from this model.
        rendered_content = Template(self.content).render(Context(context))

        sanitized = sanitize_content(rendered_content)

        # render the content in the system-controlled wrapper template
        default_template = get_template("confirmation_mail.html")
        return default_template.render({"body": mark_safe(sanitized)})

    def clean(self):
        try:
            Template(self.content)
        except TemplateSyntaxError as e:
            raise ValidationError(e)
        return super().clean()
