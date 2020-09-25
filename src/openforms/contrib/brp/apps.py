from django.apps import AppConfig


class BRPConfig(AppConfig):
    name = "openforms.contrib.brp"

    def ready(self):
        from . import field_types  # noqa
