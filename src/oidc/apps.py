from django.apps import AppConfig


class OIDCAppConfig(AppConfig):
    name = "oidc"

    def ready(self) -> None:
        from . import plugins  # noqa
