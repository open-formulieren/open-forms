from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DemoOutageApp(AppConfig):
    name = "openforms.authentication.contrib.outage"
    label = "authentication_outage"
    verbose_name = _("Always outage authentication plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
