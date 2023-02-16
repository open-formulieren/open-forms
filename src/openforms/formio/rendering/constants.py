from django.db import models
from django.utils.translation import gettext_lazy as _


class RenderConfigurationOptions(models.TextChoices):
    show_in_summary = "showInSummary", _("Show in summary")
    show_in_pdf = "showInPDF", _("Show in PDF")
    show_in_confirmation_email = "showInEmail", _("Show in confirmation email")
