from django.db import models
from django.utils.translation import gettext_lazy as _


class AttachmentFormat(models.TextChoices):
    pdf = "pdf", _("PDF")
    csv = "csv", _("CSV")
    xlsx = "xlsx", _("Excel")
