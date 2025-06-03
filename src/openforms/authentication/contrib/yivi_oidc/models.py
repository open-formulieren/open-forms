from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.models.eherkenning import AuthorizeeMixin
from mozilla_django_oidc_db.models import OpenIDConnectConfigBase


def get_callback_view(self):
    from .views import callback_view

    return callback_view


class YiviOpenIDConnectConfig(AuthorizeeMixin, OpenIDConnectConfigBase):
    class Meta:
        verbose_name = _("Yivi (OIDC)")
        verbose_name_plural = _("Yivi (OIDC)")

    get_callback_view = get_callback_view
    of_oidcdb_required_claims = []

    @classproperty
    def oidc_authentication_callback_url(cls) -> str:
        return "oidc_authentication_callback"
