from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from .constants import AppointmentDetailsStatus, AppointmentsConfigPaths


class AppointmentsConfig(SingletonModel):
    config_path = models.CharField(
        _("config path"),
        choices=AppointmentsConfigPaths,
        max_length=255,
        blank=True,
    )


class AppointmentInfo(models.Model):

    status = models.CharField(
        _("status"),
        choices=AppointmentDetailsStatus,
        max_length=50,
    )
    appointment_id = models.CharField(
        _("status"),
        max_length=50,
        blank=True,
    )
    error_information = models.TextField(
        _("error information"),
        blank=True,
    )

    submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="+",
        help_text=_("The submission that made the appointment"),
    )
