from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DemoConfig(AppConfig):
    name = "openforms.appointments.contrib.demo"
    verbose_name = _("Demo appointment plugin")

    def ready(self):
        from . import plugin  # noqa
