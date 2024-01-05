from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BRKApp(AppConfig):
    name = "openforms.contrib.brk"
    label = "brk"
    verbose_name = _("BRK configuration")

    def ready(self):
        # register the plugin
        from . import validators  # noqa
