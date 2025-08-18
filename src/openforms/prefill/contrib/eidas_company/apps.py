from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EIDASCompanyApp(AppConfig):
    name = "openforms.prefill.contrib.eidas_company"
    label = "prefill_eidas_company"
    verbose_name = _("eIDAS company prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
