from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.models import OpenIDConnectConfig

from ...constants import AuthAttribute
from ...registry import register
from ..digid_eherkenning_oidc.plugin import OIDCAuthentication
from .constants import AZURE_AD_OIDC_AUTH_SESSION_KEY


@register("azure_ad_oidc")
class AzureADOIDCAuthenticationPlugin(OIDCAuthentication):
    verbose_name = _("Azure AD via OpenID Connect")
    provides_auth = AuthAttribute.employee_id
    session_key = AZURE_AD_OIDC_AUTH_SESSION_KEY
    config_class = OpenIDConnectConfig
