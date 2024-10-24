from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OpenProductenConfig(AppConfig):
    name = "openforms.contrib.open_producten"
    label = "open_producten"
    verbose_name = _("Open Producten configuration")
