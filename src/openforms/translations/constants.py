from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusChoices(models.TextChoices):
    in_progress = "in_progress", _("In progress")
    pending = "pending", _("Pending")
    done = "done", _("Done")
    failed = "failed", _("Failed")
