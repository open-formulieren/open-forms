import warnings

from django.conf import settings
from django.utils.functional import classproperty

from mozilla_django_oidc_db.models import OpenIDConnectConfig


class OrgOpenIDConnectConfig(OpenIDConnectConfig):
    class Meta:
        proxy = True

    @classproperty
    def oidcdb_check_idp_availability(cls) -> bool:
        return True

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:  # type: ignore
        if settings.USE_LEGACY_ORG_OIDC_ENDPOINTS:
            warnings.warn(
                "Legacy DigiD-eHerkenning callback endpoints will be removed in 3.0",
                DeprecationWarning,
            )
            return "org-oidc-callback"
        return "oidc_authentication_callback"

    def get_callback_view(self):
        from .views import callback_view

        return callback_view
