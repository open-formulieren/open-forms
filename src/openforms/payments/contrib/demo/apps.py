from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DemoApp(AppConfig):
    name = "openforms.payments.contrib.demo"
    label = "payments_demo"
    verbose_name = _("Demo payments plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
