from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SuwinetApp(AppConfig):
    name = "openforms.prefill.contrib.suwinet"
    label = "prefill_suwinet"
    verbose_name = _("Suwinet prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
