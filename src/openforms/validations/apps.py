from django.apps import AppConfig


class ValidationsConfig(AppConfig):
    name = "openforms.validations"
    label = "validations"

    def ready(self):
        from .validators import formats  # noqa
