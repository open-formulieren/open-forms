from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class KlantinteractiesApp(AppConfig):
    name = "openforms.contrib.klantinteracties"
    label = "klantinteracties"
    verbose_name = _("Klantinteracties")
