from django.apps import AppConfig


class JCCAfsprakenPlugin(AppConfig):
    name = "openforms.appointments.contrib.jcc"
    verbose_name = "JCC-Afspraken appointment plugin"

    def ready(self):
        from . import plugin  # noqa
