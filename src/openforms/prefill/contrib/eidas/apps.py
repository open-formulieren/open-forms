from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EIDASApp(AppConfig):
    name = "openforms.prefill.contrib.eidas"
    label = "prefill_eidas"
    verbose_name = _("eIDAS prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
