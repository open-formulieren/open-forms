from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WorldlineApp(AppConfig):
    name = "openforms.payments.contrib.worldline"
    label = "payments_worldline"
    verbose_name = _("Worldline payment plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
