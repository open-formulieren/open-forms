from django.apps import AppConfig


class ZGWRestPlugin(AppConfig):
    name = "openforms.registrations.contrib.zgw_apis"
    verbose_name = "Zaakgericht werken API's plugin"

    def ready(self):
        from . import plugin  # noqa
