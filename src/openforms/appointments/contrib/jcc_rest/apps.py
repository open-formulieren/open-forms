from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class JCCRESTPluginConfig(AppConfig):
    name = "openforms.appointments.contrib.jcc_rest"
    verbose_name = _("JCC REST appointment plugin")

    def ready(self):
        from . import plugin  # noqa
