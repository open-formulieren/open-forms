from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ZGWRestPlugin(AppConfig):
    name = "openforms.registrations.contrib.zgw_apis"
    verbose_name = _("ZGW API's plugin")

    def ready(self):
        from . import plugin  # noqa
