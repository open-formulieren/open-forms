from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DigidApp(AppConfig):
    name = "openforms.authentication.contrib.digid"
    label = "prefill_digid"
    verbose_name = _("Digid authentication plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
