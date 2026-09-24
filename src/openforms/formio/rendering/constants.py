from django.db import models
from django.utils.translation import gettext_lazy as _


class RenderConfigurationOptions(models.TextChoices):
    show_in_summary = "show_in_summary", _("Show in summary")
    show_in_pdf = "show_in_pdf", _("Show in PDF")
    show_in_confirmation_email = "show_in_email", _("Show in confirmation email")
