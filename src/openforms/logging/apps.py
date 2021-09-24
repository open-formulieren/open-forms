from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LoggingAppConfig(AppConfig):
    name = "openforms.logging"
    verbose_name = _("Logging")
