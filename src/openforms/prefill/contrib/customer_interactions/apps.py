from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommunicationPreferencesApp(AppConfig):
    name = "openforms.prefill.contrib.customer_interactions"
    label = "prefill_customer_interactions"
    verbose_name = _("Customer interactions API prefill plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
