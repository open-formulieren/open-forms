from typing import Any, Dict

from django.db import models
from django.template import Context, Template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openforms.appointments.models import AppointmentInfo
from openforms.submissions.models import Submission

from ..utils.urls import build_absolute_uri
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
        if submission.payment_required:
            context["payment_required"] = True
            context["payment_user_has_paid"] = submission.payment_user_has_paid
            context["payment_url"] = build_absolute_uri(
                reverse("payments:link", kwargs={"uuid": submission.uuid})
            )
            context["payment_price"] = str(submission.form.product.price)

        try:
            context["_appointment_id"] = submission.appointment_info.appointment_id
        except AppointmentInfo.DoesNotExist:
            pass

        return context

    def render(self, submission: Submission):
        context = self.get_context_data(submission)

        # render the e-mail body - the template from this model.
        rendered_content = Template(self.content).render(Context(context))

        return rendered_content

    # def clean(self):
    #     self.validate_content()
    #     return super().clean()
