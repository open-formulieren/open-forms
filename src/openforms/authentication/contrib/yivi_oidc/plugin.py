from typing import TypedDict

from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.views import _RETURN_URL_SESSION_KEY

from openforms.forms.models import Form
from openforms.utils.urls import reverse_plus

from ...base import BasePlugin, LoginLogo
from ...constants import FORM_AUTH_SESSION_KEY, AuthAttribute, LogoAppearance
from ...registry import register
from ...typing import FormAuth
from .config import YiviOptions, YiviOptionsSerializer
from .constants import PLUGIN_ID
from .models import YiviOpenIDConnectConfig
from .views import OIDCAuthenticationInitView

yivi_init = OIDCAuthenticationInitView.as_view(
    config_class=YiviOpenIDConnectConfig,
    allow_next_from_query=False,
)


class YiviClaims(TypedDict, total=False):
    """
    Processed Yivi claims structure.

    See :attr:`openforms.authentication.yivi_oidc.models` for the source of this
    structure.

    All attributes are optional, as some attributes are only present when user
    login using certain authentication methods (i.e. only when the user logs in
    using bsn, is the bsn claim available).

    `additional_claims` could contain additional attributes received during login.
    This depends on the used Yivi `AdditionalAttributes` by the form, and which
    attributes the user decided to provide.
    The names of these additional attributes/claims are unpredictable: when defining
    the Yivi `AdditionalAttributes`, the admins can assign any attribute they want
    (as different municipalities probably will use different Yivi attribute-sets).
    The names of these attributes will also be used for the claims, so
    `additional_claims` could contain a claim named
    "irma-demo.gemeente.personalData.fullname".
    """

    # Claims for auth attribute bsn
    bsn_claim: str

    # Claims for auth attribute kvk
    kvk_claim: str

    # Claims for anonymous/pseudo authentication
    pseudo_claim: str

    # *could* be a number if no value mapping is specified and the source claims return
    # numeric values...
    loa_claim: str | int | float

    # Mapping for additionally fetched claims
    additional_claims: dict[str, str]


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

    @staticmethod
    def _get_user_chosen_authentication_attribute(
        authentication_options: list[AuthAttribute],
        normalized_claims: YiviClaims,
    ) -> AuthAttribute:
        """
        Return the user chosen authentication attribute.
        User chosen authentication attribute is defined based on the provided claims. To
        make sure that the plugin allows the specific authentication attribute, the
        defined authentication_options must contain the presumed authentication
        attribute.
        """

        bsn = bool(normalized_claims.get("bsn_claim"))
        kvk = bool(normalized_claims.get("kvk_claim"))

        if AuthAttribute.bsn in authentication_options and bsn:
            return AuthAttribute.bsn
        elif AuthAttribute.kvk in authentication_options and kvk:
            return AuthAttribute.kvk
        else:
            return AuthAttribute.pseudo

    def transform_claims(
        self, options: YiviOptions, normalized_claims: YiviClaims
    ) -> FormAuth:
        authentication_options = options["authentication_options"]
        authentication_attribute = self._get_user_chosen_authentication_attribute(
            authentication_options, normalized_claims
        )

        form_auth = {
            "attribute": authentication_attribute,
            "plugin": self.identifier,
            "additional_claims": normalized_claims.get("additional_claims", {}),
        }

        # Set form authentication values based on the used authentication option
        match authentication_attribute:
            case AuthAttribute.bsn:
                # Copied from digid_oidc
                form_auth["value"] = normalized_claims["bsn_claim"]
                form_auth["loa"] = str(normalized_claims.get("loa_claim", ""))

            case AuthAttribute.kvk:
                # Copied from eherkenning_oidc
                form_auth["value"] = normalized_claims["kvk_claim"]
                form_auth["loa"] = str(normalized_claims.get("loa_claim", ""))

            case AuthAttribute.pseudo:
                form_auth["value"] = (
                    normalized_claims.get("pseudo_claim", "")
                    or "dummy-set-by@openforms"
                )

        return form_auth

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str, options: YiviOptions
    ):
        return_url = reverse_plus(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
            query={"next": form_url},
        )

        response = yivi_init(request, return_url=return_url, options=options)
        assert isinstance(response, HttpResponseRedirect)
        return response

    def handle_return(self, request, form, options: YiviOptions):
        """
        Redirect to form URL.
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        normalized_claims: YiviClaims | None = request.session.get(self.session_key)
        if normalized_claims:
            request.session[FORM_AUTH_SESSION_KEY] = self.transform_claims(
                options, normalized_claims
            )

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        keys_to_delete = (
            "oidc_id_token",
            "oidc_login_next",
            self.session_key,
            _RETURN_URL_SESSION_KEY,
        )
        for key in keys_to_delete:
            if key in request.session:
                del request.session[key]

    def get_label(self):
        return "Yivi"

    def get_logo(self, request: HttpRequest) -> LoginLogo:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/yivi.png")),
            href="https://yivi.app/",
            appearance=LogoAppearance.light,
        )
