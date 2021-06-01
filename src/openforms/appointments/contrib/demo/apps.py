from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DemoAppConfig(AppConfig):
    name = "openforms.appointments.contrib.demo"
    label = "appointments.demo"
    verbose_name = _("Demo appointment plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
