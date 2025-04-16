from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class YiviOIDCApp(AppConfig):
    name = "openforms.authentication.contrib.yivi_oidc"
    label = "authentication_yivi_oidc_oidc"
    verbose_name = _("Yivi OpenID Connect authentication plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
