from django.apps import AppConfig


class ZgwAppConfig(AppConfig):
    name = "openforms.contrib.zgw"

    def ready(self):
        from . import backends  # noqa
