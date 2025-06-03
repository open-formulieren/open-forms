from typing import TypedDict

from django.contrib import auth
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.views import OIDCInit

from openforms.accounts.models import User
from openforms.forms.models import Form
from openforms.utils.urls import reverse_plus

from ...base import BasePlugin, LoginLogo
from ...constants import FORM_AUTH_SESSION_KEY, AuthAttribute, LogoAppearance
from ...registry import register
from .config import YiviOptions, YiviOptionsSerializer
from .constants import PLUGIN_ID
from .models import YiviOpenIDConnectConfig

yivi_init = OIDCInit.as_view(
    config_class=YiviOpenIDConnectConfig,
    allow_next_from_query=False,
)


class YiviClaims(TypedDict):
    """
    Processed Yivi claims structure.

    See :attr:`openforms.authentication.yivi_oidc.models` for the source of this
    structure.
    """


@register(PLUGIN_ID)
class YiviOIDCAuthentication(BasePlugin[YiviOptions]):
    """
    Authentication plugin using the global mozilla-django-oidc-db (as used for the admin)
    """

    session_key: str = "yivi_oidc"
    verbose_name = _("Yivi via OpenID Connect")
    # Yivi can provide a range of auth attributes, including bsn and kvk
    provides_auth = (AuthAttribute.bsn, AuthAttribute.kvk, AuthAttribute.pseudo)
    config_class = YiviOpenIDConnectConfig
    configuration_options = YiviOptionsSerializer

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str, options: YiviOptions
    ):
        return_url = reverse_plus(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
            query={"next": form_url},
        )

        response = yivi_init(request, return_url=return_url)
        assert isinstance(response, HttpResponseRedirect)
        return response

    def handle_return(self, request, form, options: YiviOptions):
        """
        Redirect to form URL.
        """
        assert request.user.is_authenticated
        assert isinstance(request.user, User)

        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        normalized_claims: YiviClaims | None = request.session.get(self.session_key)
        if normalized_claims:
            form_auth = {
                "plugin": self.identifier,
                "attribute": AuthAttribute,
                "value": "some yivi claim",
            }
            request.session[FORM_AUTH_SESSION_KEY] = form_auth

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        # @TODO not sure if this is all
        for key in (
            "oidc_id_token",
            "oidc_login_next",
            self.session_key,
        ):
            if key in request.session:
                del request.session[key]

        if request.user.is_authenticated:
            auth.logout(request)
            assert not request.user.is_authenticated

    def get_label(self):
        return "Yivi"

    def get_logo(self, request: HttpRequest) -> LoginLogo:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/yivi.png")),
            href="https://yivi.app/",
            appearance=LogoAppearance.light,
        )
