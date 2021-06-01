from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QmaticPluginAppConfig(AppConfig):
    name = "openforms.appointments.contrib.qmatic"
    label = "appointments.qmatic"
    verbose_name = _("Qmatic appointment plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
