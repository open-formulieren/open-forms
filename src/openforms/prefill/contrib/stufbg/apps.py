from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StufBgApp(AppConfig):
    name = "openforms.prefill.contrib.stufbg"
    label = "prefill.stufbg"
    verbose_name = _("StUF-BG prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
