from django.db import models
from django.utils.translation import gettext_lazy as _


class TimelineLogTags(models.TextChoices):
    AVG = "avg", _("AVG")
    hijack = "hijack", _("Hijack")
    submission_lifecycle = "submission_lifecycle", _("Submission lifecycle")


FORM_SUBMIT_SUCCESS_EVENT = "form_submit_success"
REGISTRATION_SUCCESS_EVENT = "registration_success"
