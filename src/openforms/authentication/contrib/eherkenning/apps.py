from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EHerkenningApp(AppConfig):
    name = "openforms.authentication.contrib.eherkenning"
    label = "authentication_eherkenning"
    verbose_name = _("eHerkenning/eIDAS authentication plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
