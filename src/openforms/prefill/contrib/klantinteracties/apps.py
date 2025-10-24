from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class KlantInteractiesApp(AppConfig):
    name = "openforms.prefill.contrib.klantinteracties"
    label = "prefill_klantinteracties"
    verbose_name = _("Klantinteracties prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
