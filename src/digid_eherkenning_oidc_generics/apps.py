from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DigiDeHerkenningOIDCAppConfig(AppConfig):
    name = "digid_eherkenning_oidc_generics"
    verbose_name = _("DigiD & eHerkenning via OpenID Connect")
