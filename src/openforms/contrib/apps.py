from django.apps import AppConfig


class ContribConfig(AppConfig):
    name = "openforms.contrib"

    def ready(self):
        # register the custom handlers
        from . import brp  # noqa
