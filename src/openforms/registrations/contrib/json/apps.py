from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


# TODO-4908: maybe rename to FVaJ (Form Variables as JSON)
class JSONAppConfig(AppConfig):
    name = "openforms.registrations.contrib.json"
    label = "registrations_json"
    verbose_name = _("JSON plugin")

    def ready(self):
        from . import plugin  # noqa
