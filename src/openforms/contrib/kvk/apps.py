from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class KVKApp(AppConfig):
    name = "openforms.contrib.kvk"
    label = "kvk"
    verbose_name = _("KvK code & configuration")

    def ready(self):
        # register the plugin
        from . import validators  # noqa
