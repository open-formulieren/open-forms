from django.db import models
from django.utils.translation import gettext_lazy as _


class SummaryDocumentChoices(models.TextChoices):
    json = "json", _("JSON document")
    pdf = "pdf", _("PDF document")
