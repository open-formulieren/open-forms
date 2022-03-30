from django.apps import AppConfig


class DMNConfig(AppConfig):
    name = "openforms.dmn"
    label = "dmn"

    def ready(self):
        from . import custom_field_types  # noqa
