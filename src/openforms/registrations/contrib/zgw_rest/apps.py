from django.apps import AppConfig


class ZGWRestPlugin(AppConfig):
    name = "openforms.registrations.contrib.zgw_rest"
    verbose_name = "ZGW plugin"

    def ready(self):
        from . import plugin  # noqa
