from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CamundaApp(AppConfig):
    name = "openforms.registrations.contrib.camunda"
    label = "registrations_camunda"
    verbose_name = _("Camunda registration plugin")

    def ready(self):
        # register plugin
        from . import plugin  # noqa
