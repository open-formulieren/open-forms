from django.utils.functional import classproperty

from mozilla_django_oidc_db.models import OpenIDConnectConfig


class YiviOpenIDConnectConfig(OpenIDConnectConfig):
    class Meta:
        proxy = True

    # @TODO does Yivi have any required claims?
    of_oidcdb_required_claims = []

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:
        return "oidc_authentication_callback"

    def get_callback_view(self):
        from .views import callback_view

        return callback_view
