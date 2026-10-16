from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InitialDataConfig(AppConfig):
    name = "openforms.initial_data"
    verbose_name = _("Initial data")
