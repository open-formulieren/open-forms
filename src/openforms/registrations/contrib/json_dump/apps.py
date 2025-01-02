from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class JSONDumpAppConfig(AppConfig):
    name = "openforms.registrations.contrib.json_dump"
    label = "registrations_json_dump"
    verbose_name = _("JSON Dump plugin")

    def ready(self):
        from . import plugin  # noqa
