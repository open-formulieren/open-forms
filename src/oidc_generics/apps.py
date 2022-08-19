from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OIDCAppConfig(AppConfig):
    name = "oidc_generics"
    verbose_name = _("OpenID Connect")
