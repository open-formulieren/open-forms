from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EIDASApp(AppConfig):
    name = "openforms.authentication.contrib.eidas"
    label = "authentication_eidas"
    verbose_name = _("eIDAS authentication plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
