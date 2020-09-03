from django.apps import AppConfig


class UtilsConfig(AppConfig):
    name = "openforms.utils"

    def ready(self):
        from . import checks  # noqa
