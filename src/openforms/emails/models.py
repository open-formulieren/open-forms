import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context, Template, TemplateSyntaxError
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from openforms.config.models import GlobalConfiguration

from .constants import URL_REGEX


class ConfirmationEmailTemplate(models.Model):
    subject = models.CharField(
        max_length=1000, help_text=_("Subject of the email message")
    )
    content = models.TextField(
        help_text=_(
            "The content of the email message, can contain variables that will be "
            "templated form the submitted form data."
        )
    )
    form = models.OneToOneField(
        "forms.Form",
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
        return default_template.render({"body": stripped})

    def clean(self):
        try:
            self.render({})
        except TemplateSyntaxError as e:
            raise ValidationError(e)
        return super().clean()
