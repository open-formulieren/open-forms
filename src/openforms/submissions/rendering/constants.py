from django.db import models
from django.utils.translation import gettext_lazy as _


class RenderModes(models.TextChoices):
    cli = "cli", _("CLI")
    pdf = "pdf", _("PDF")
    summary = "summary", _("Summary page")
    confirmation_email = "confirmation_email", _("Confirmation email")
    export = "export", _("Submission export")
    registration = "registration", _("Registration")
