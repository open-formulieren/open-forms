from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class KadasterAPIConfig(AppConfig):
    name = "openforms.contrib.kadaster"
    label = "contrib_kadaster"
    verbose_name = _("Kadaster API")
