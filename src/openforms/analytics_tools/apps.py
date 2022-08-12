from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AnalyticsToolsConfig(AppConfig):
    name = "openforms.analytics_tools"
    verbose_name = _("Analytics tools")
