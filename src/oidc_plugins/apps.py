from django.apps import AppConfig


class OIDCAppConfig(AppConfig):
    name = "oidc_plugins"

    def ready(self) -> None:
        from . import plugins  # noqa
