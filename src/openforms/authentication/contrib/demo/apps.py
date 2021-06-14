from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DemoApp(AppConfig):
    name = "openforms.authentication.contrib.demo"
    label = "authentication_demo"
    verbose_name = _("Demo authentication plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
