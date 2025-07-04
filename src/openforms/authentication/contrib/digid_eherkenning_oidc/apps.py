from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DigiDEHerkenningOIDCApp(AppConfig):
    name = "openforms.authentication.contrib.digid_eherkenning_oidc"
    label = "digid_eherkenning_oidc"
    verbose_name = _("DigiD/eHerkenning via OpenID Connect")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
        from .oidc_plugins import plugins as oidc_plugins  # noqa
