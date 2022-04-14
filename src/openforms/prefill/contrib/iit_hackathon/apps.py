from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HaalCentraalApp(AppConfig):
    name = "openforms.prefill.contrib.iit_hackathon"
    label = "prefill_iit_hackathon"
    verbose_name = _("IIT Hackathon prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
