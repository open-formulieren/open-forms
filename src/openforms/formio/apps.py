from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FormioConfig(AppConfig):
    name = "openforms.formio"
    verbose_name = _("Formio integration")

    def ready(self):
        from .components import register_all

        register_all()
