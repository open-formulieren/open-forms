from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class eHerkenningOIDCApp(AppConfig):
    name = "openforms.authentication.contrib.eherkenning_oidc"
    label = "eherkenning_oidc"
    verbose_name = _("eHerkenning via OpenID Connect")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
