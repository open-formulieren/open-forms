import re
from typing import List
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context, Template, TemplateSyntaxError
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from openforms.config.models import GlobalConfiguration

from ..forms.models import FormDefinition
from .constants import URL_REGEX


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
        on_delete=models.DO_NOTHING,
        related_name="confirmation_email_template",
        help_text=_("The form for which this confirmation email template will be used"),
    )

    class Meta:
        verbose_name = _("Confirmation email template")
        verbose_name_plural = _("Confirmation email templates")

    def __str__(self):
        return f"Confirmation email template - {self.form}"

    def render(self, context):
        config = GlobalConfiguration.get_solo()

        def replace_urls(match):
            parsed = urlparse(match.group())
            if parsed.netloc in config.email_template_netloc_allowlist:
                return match.group()
            return ""

        default_template = get_template("confirmation_mail.html")
        rendered_content = Template(self.content).render(Context(context))
        stripped = re.sub(URL_REGEX, replace_urls, rendered_content)

        processed_context = {"body": stripped, "show_summary": False}

        # Check if the confirmation email should contain a summary of the submitted data
        if re.search(r"\{\{ summary \}\}", self.content):
            filtered_data = self.filter_data_to_show_in_email(context)
            processed_context["show_summary"] = True
            processed_context["summary"] = filtered_data

        return default_template.render(processed_context)

    def filter_data_to_show_in_email(self, submitted_data: dict) -> dict:
        """Extract data that should be shown as a summary of submission in the confirmation email"""

        # From the form definition, see which fields should be shown in the confirmation email
        data_to_show_in_email = []
        for form_definition in FormDefinition.objects.filter(formstep__form=self.form):
            components = form_definition.configuration.get("configuration").get(
                "components"
            )
            if components:
                for component in components:
                    if component.get("showInEmail"):
                        data_to_show_in_email.append(component["key"])

        # Return a dict with only the data that should be shown in the email
        filtered_data = {}
        for property in data_to_show_in_email:
            if property in submitted_data:
                filtered_data[property] = submitted_data[property]
        return filtered_data

    def clean(self):
        try:
            self.render({})
        except TemplateSyntaxError as e:
            raise ValidationError(e)
        return super().clean()
