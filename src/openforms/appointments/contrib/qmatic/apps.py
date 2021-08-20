from django.apps import AppConfig


class QmaticPlugin(AppConfig):
    name = "openforms.appointments.contrib.qmatic"
    verbose_name = "Qmatic appointment plugin"

    def ready(self):
        from . import plugin  # noqa
