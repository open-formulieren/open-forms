from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ObjectsApiApp(AppConfig):
    name = "openforms.prefill.contrib.objects_api"
    label = "prefill_objects_api"
    verbose_name = _("Objects API prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
