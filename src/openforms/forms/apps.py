from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "openforms.forms"
    verbose_name = "OpenForms Form App"

    def ready(self) -> None:
        # register async metrics
        from . import metrics  # noqa
