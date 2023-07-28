from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HaalCentraalHRApp(AppConfig):
    name = "openforms.prefill.contrib.haalcentraal_hr"
    label = "prefill_haalcentraal_hr"
    verbose_name = _("Haal Centraal HR")

    def ready(self):
        from . import plugin  # noqa
