from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HaalCentraalConfig(AppConfig):
    name = "openforms.contrib.haal_centraal"
    label = "haalcentraal"
    verbose_name = _("Haal Centraal configuration")
