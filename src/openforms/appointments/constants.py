from django.db import models
from django.utils.translation import gettext_lazy as _


class AppointmentDetailsStatus(models.TextChoices):
    success = "success", _("Success")
    missing_info = "missing_info", _(
        "Submission does not contain all the info needed to make an appointment"
    )
    failed = "failed", _("Failed")
    cancelled = "cancelled", _("Cancelled")
