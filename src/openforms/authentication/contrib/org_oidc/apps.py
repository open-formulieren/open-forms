from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrgOIDCApp(AppConfig):
    name = "openforms.authentication.contrib.org_oidc"
    label = "authentication_org_oidc"
    verbose_name = _("Organization OpenID Connect authentication plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa
        from .oidc_plugins import plugins as oidc_plugins  # noqa
