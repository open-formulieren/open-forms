from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GenericJSONAppConfig(AppConfig):
    name = "openforms.registrations.contrib.generic_json"
    label = "registrations_generic_json"
    verbose_name = _("Generic JSON registration")

    def ready(self):
        from . import plugin  # noqa
