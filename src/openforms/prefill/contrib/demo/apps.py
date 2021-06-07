from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DemoApp(AppConfig):
    name = "openforms.prefill.contrib.demo"
    label = "prefill_demo"
    verbose_name = _("Demo prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
