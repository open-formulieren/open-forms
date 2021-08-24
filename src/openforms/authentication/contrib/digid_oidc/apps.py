from django.apps import AppConfig


class DigiDOIDCApp(AppConfig):
    name = "openforms.authentication.contrib.digid_oidc"
    label = "digid_oidc"
    verbose_name = "DigiD via OpenID Connect"

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
