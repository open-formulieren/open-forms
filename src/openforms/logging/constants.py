from django.db import models
from django.utils.translation import gettext_lazy as _


class TimelineLogTags(models.TextChoices):
    AVG = "avg", _("AVG")
    hijack = "hijack", _("Hijack")
    submission_lifecycle = "submission_lifecycle", _("Submission lifecycle")
