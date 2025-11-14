from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommunicationPreferencesApp(AppConfig):
    name = "openforms.prefill.contrib.communication_preferences"
    label = "prefill_communication_preferences"
    verbose_name = _("Communication preferences prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
