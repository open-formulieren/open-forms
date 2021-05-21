import re
from functools import partial
from typing import Any, Dict, List
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context, Template, TemplateSyntaxError
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from openforms.config.models import GlobalConfiguration
from openforms.submissions.models import Submission

from .constants import URL_REGEX


def sanitize_urls(allowlist: List[str], match) -> str:
    parsed = urlparse(match.group())
    if parsed.netloc in allowlist:
        return match.group()
    return ""


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

    @staticmethod
    def get_context_data(submission: Submission) -> Dict[str, Any]:
        context = {
            # use private variables that can't be accessed in the template data, so that
            # template designers can't call the .delete method, for example. Variables
            # starting with underscores are blocked by the Django template engine.
            "_submission": submission,
            "_form": submission.form,  # should be the same as self.form
            **submission.data,
        }
        return context

    def render(self, submission: Submission):
        config = GlobalConfiguration.get_solo()
        context = self.get_context_data(submission)

        # render the e-mail body - the template from this model.
        rendered_content = Template(self.content).render(Context(context))

        # strip out any hyperlinks that are not in the configured allowlist
        replace_urls = partial(sanitize_urls, config.email_template_netloc_allowlist)
        stripped = re.sub(URL_REGEX, replace_urls, rendered_content)

        # render the content in the system-controlled wrapper template
        default_template = get_template("confirmation_mail.html")
        return default_template.render({"body": mark_safe(stripped)})

    def clean(self):
        try:
            Template(self.content)
        except TemplateSyntaxError as e:
            raise ValidationError(e)
        return super().clean()
