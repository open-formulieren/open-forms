from django.apps import AppConfig


class StufZDSPlugin(AppConfig):
    name = "openforms.registrations.contrib.stuf_zds"
    verbose_name = " StUF-ZDS registration plugin"

    def ready(self):
        from . import plugin  # noqa
