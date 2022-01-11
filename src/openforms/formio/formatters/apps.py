from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FormIOFormattersApp(AppConfig):
    name = "openforms.formio.formatters"
    label = "formio_formatters"
    verbose_name = _("FormIO formatters")

    def ready(self):
        # register the plugin
        from . import default  # noqa
