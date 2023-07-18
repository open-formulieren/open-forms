from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SOAPAppConfig(AppConfig):
    name = "soap"
    verbose_name = _("SOAP Settings & Services")
