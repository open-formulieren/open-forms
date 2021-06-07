from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DemoConfig(AppConfig):
    name = "openforms.registrations.contrib.demo"
    label = "registrations_demo"
    verbose_name = _("Demo registrations plugin")

    def ready(self):
        # register plugin
        from . import plugin  # noqa
