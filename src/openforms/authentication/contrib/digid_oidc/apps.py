from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DigiDOIDCApp(AppConfig):
    name = "openforms.authentication.contrib.digid_oidc"
    label = "digid_oidc"
    verbose_name = _("DigiD via OpenID Connect")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
