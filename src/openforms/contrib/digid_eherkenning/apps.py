from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DigidEherkenningApp(AppConfig):
    name = "openforms.contrib.digid_eherkenning"
    label = "contrib_digid_eherkenning"
    verbose_name = _("DigiD/Eherkenning utilities")

    def ready(self):
        # register the signals
        from .signals import trigger_csp_update  # noqa
