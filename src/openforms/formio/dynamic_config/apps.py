from django.apps import AppConfig


class FormioDynamicConfigApp(AppConfig):
    name = "openforms.formio.dynamic_config"
    label = "formio_dynamic_config"

    def ready(self):
        from . import date  # noqa - register the plugins
