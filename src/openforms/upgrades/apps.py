from django.apps import AppConfig


class UpgradesConfig(AppConfig):
    name = "openforms.upgrades"

    def ready(self):
        from . import checks  # noqa
        from . import signals  # noqa
