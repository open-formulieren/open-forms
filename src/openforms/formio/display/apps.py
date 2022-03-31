from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FormIODisplayApp(AppConfig):
    name = "openforms.formio.display"
    label = "formio_display"
    verbose_name = _("FormIO display")

    def ready(self):
        # register the plugin
        from . import default  # noqa
