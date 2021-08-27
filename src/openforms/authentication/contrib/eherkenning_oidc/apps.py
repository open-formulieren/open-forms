from django.apps import AppConfig


class eHerkenningOIDCApp(AppConfig):
    name = "openforms.authentication.contrib.eherkenning_oidc"
    label = "eherkenning_oidc"
    verbose_name = "eHerkenning via OpenID Connect"

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
