from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DigidMockApp(AppConfig):
    name = "openforms.authentication.contrib.digid_mock"
    label = "authentication_digid_mock"
    verbose_name = _("DigiD Mock authentication plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
