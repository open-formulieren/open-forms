from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from .constants import AppointmentsConfigPaths


class AppointmentsConfig(SingletonModel):
    config_path = models.CharField(
        _("config path"),
        choices=AppointmentsConfigPaths,
        max_length=255,
        blank=True,
    )
