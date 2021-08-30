from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class AppointmentsConfig(SingletonModel):
    config_path = models.CharField(
        _("config path"),
        choices=(
            ("openforms.appointments.contrib.jcc.models.JccConfig", "Jcc"),
            ("openforms.appointments.contrib.qmatic.models.QmaticConfig", "Qmatic"),
        ),
        max_length=255,
        blank=True,
    )
