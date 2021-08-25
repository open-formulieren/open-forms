from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QmaticPlugin(AppConfig):
    name = "openforms.appointments.contrib.qmatic"
    verbose_name = _("Qmatic appointment plugin")

    def ready(self):
        from . import plugin  # noqa
