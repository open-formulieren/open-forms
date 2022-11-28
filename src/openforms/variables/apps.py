from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class Variables(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "openforms.variables"
    verbose_name = _("Variables")
