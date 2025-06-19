from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class YiviOIDCApp(AppConfig):
    name = "openforms.authentication.contrib.yivi_oidc"
    label = "yivi_oidc"
    verbose_name = _("Yivi via OpenID Connect")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
