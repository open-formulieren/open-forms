from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class KVKApp(AppConfig):
    name = "openforms.prefill.contrib.kvk"
    label = "prefill_kvk"
    verbose_name = _("KvK prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
