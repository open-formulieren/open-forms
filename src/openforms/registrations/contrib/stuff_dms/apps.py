from django.apps import AppConfig


class StufDMSPlugin(AppConfig):
    name = "openforms.registrations.contrib.stuff_dms"
    verbose_name = " StUF-DMS registration plugin"

    def ready(self):
        from . import plugin  # noqa
