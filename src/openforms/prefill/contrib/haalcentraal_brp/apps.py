from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HaalCentraalBRPApp(AppConfig):
    name = "openforms.prefill.contrib.haalcentraal_brp"
    label = "prefill_haalcentraal"
    verbose_name = _("Haal Centraal: BRP Personen Bevragen prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
