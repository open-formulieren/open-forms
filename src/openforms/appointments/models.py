from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from .constants import AppointmentDetailsStatus, AppointmentsConfigPaths


class AppointmentsConfig(SingletonModel):
    config_path = models.CharField(
        _("appointment plugin"),
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
        _("appointment ID"),
        max_length=50,
        blank=True,
    )
    error_information = models.TextField(
        _("error information"),
        blank=True,
    )
    start_time = models.DateTimeField(
        _("start time"),
        blank=True,
        null=True,
        help_text=_("Start time of the appointment"),
    )

    submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="appointment_info",
        help_text=_("The submission that made the appointment"),
    )

    created = models.DateTimeField(
        _("created"),
        auto_now_add=True,
        help_text=_("Timestamp when the appointment details were created"),
    )

    class Meta:
        verbose_name = _("Appointment information")
        verbose_name_plural = _("Appointment information")

    def __str__(self):
        status = self.get_status_display()
        description = self.appointment_id or self.error_information[:20]
        return f"{status}: {description}"

    def cancel(self):
        self.status = AppointmentDetailsStatus.cancelled
        self.save()
