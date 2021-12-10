from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PrefillConfig(AppConfig):
    name = "openforms.prefill"
    verbose_name = _("Prefill")

    def ready(self):
        # register signal receivers
        # ensure that validators are registered
        from . import signals  # noqa
        from . import validators  # noqa
