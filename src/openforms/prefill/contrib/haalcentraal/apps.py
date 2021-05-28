from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HaalCentraalApp(AppConfig):
    name = "openforms.prefill.contrib.haalcentraal"
    label = "prefill.haalcentraal"
    verbose_name = _("Haal Centraal prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
