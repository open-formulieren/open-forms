from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MicrosoftApp(AppConfig):
    name = "openforms.contrib.microsoft"
    label = "microsoft"
    verbose_name = _("Microsoft code & configuration")
