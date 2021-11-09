from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MicrosoftGraphApp(AppConfig):
    name = "openforms.registrations.contrib.microsoft_graph"
    label = "registrations_microsoft_graph"
    verbose_name = _("Microsoft Graph registrations plugin")

    def ready(self):
        # register plugin
        from . import plugin  # noqa
