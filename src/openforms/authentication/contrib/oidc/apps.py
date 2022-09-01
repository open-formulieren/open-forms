from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OIDCApp(AppConfig):
    name = "openforms.authentication.contrib.oidc"
    label = "oidc"
    verbose_name = _("OpenID Connect")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
