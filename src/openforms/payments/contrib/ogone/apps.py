from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OgoneApp(AppConfig):
    name = "openforms.payments.contrib.ogone"
    label = "payments_ogone"
    verbose_name = _("Ogone payment plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
