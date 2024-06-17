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
        return "authentication:org-oidc-callback"

    def get_callback_view(self):
        from .views import callback_view

        return callback_view
