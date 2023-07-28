from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class KadasterAPIConfig(AppConfig):
    name = "openforms.contrib.kadaster"
    label = "kadaster"
    verbose_name = _("Kadaster")
