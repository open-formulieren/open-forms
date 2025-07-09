from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class YiviApp(AppConfig):
    name = "openforms.prefill.contrib.yivi"
    label = "prefill_yivi"
    verbose_name = _("Yivi prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
