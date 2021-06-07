from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EmailPluginConfig(AppConfig):
    name = "openforms.registrations.contrib.email"
    label = "registrations_email"
    verbose_name = _("Email plugin")

    def ready(self):
        # register plugin
        from . import plugin  # noqa
