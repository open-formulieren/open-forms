from django.apps import AppConfig


class CamundaConfig(AppConfig):
    name = "openforms.dmn.contrib.camunda"
    label = "dmn_camunda"

    def ready(self):
        from . import plugin  # noqa
