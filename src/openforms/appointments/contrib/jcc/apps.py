from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class JccPlugin(AppConfig):
    name = "openforms.appointments.contrib.jcc"
    verbose_name = _("JCC appointment plugin")

    def ready(self):
        from . import plugin  # noqa
