from typing import Any, ClassVar, Protocol

from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseBase,
    HttpResponseRedirect,
)
from django.utils.translation import gettext_lazy as _

import requests
from furl import furl
from rest_framework.reverse import reverse

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDMachtigenConfig,
    OpenIDConnectEHerkenningBewindvoeringConfig,
    OpenIDConnectEHerkenningConfig,
    OpenIDConnectPublicConfig,
)
from digid_eherkenning_oidc_generics.views import (
    digid_init,
    digid_machtigen_init,
    eherkenning_bewindvoering_init,
    eherkenning_init,
)
from openforms.contrib.digid_eherkenning.utils import (
    get_digid_logo,
    get_eherkenning_logo,
)
from openforms.forms.models import Form

from ...base import BasePlugin, LoginLogo
from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from ...registry import register
from .constants import (
    DIGID_MACHTIGEN_OIDC_AUTH_SESSION_KEY,
    DIGID_OIDC_AUTH_SESSION_KEY,
    EHERKENNING_BEWINDVOERING_OIDC_AUTH_SESSION_KEY,
    EHERKENNING_OIDC_AUTH_SESSION_KEY,
)


class AuthInit(Protocol):
    def __call__(
        self, request: HttpRequest, return_url: str, *args, **kwargs
    ) -> HttpResponseBase: ...


class OIDCAuthentication(BasePlugin):
    verbose_name = ""
    provides_auth = ""
    session_key = ""
    config_class = None
    init_view: ClassVar[AuthInit]

    def start_login(self, request: HttpRequest, form: Form, form_url: str):
        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
        )
        return_url = furl(auth_return_url).set({"next": form_url})
        if co_sign_param := request.GET.get(CO_SIGN_PARAMETER):
            return_url.args[CO_SIGN_PARAMETER] = co_sign_param

        # "evaluate" the view, this achieves two things:
        #
        # * we save a browser redirect cycle since we get the redirect to the identity
        #   provider immediately
        # * we control the config to apply 100% server side rather than passing it as
        #   a query parameter, which prevents a malicious user from messing with the
        #   redirect URL
        #
        # This may raise `OIDCProviderOutage`, which bubbles into the generic auth
        # start_view and gets handled there.
        response = self.init_view(request, return_url=str(return_url))
        assert isinstance(response, HttpResponseRedirect)
        return response

    def handle_co_sign(self, request: HttpRequest, form: Form) -> dict[str, Any] | None:
        if not (claim := request.session.get(self.session_key)):
            raise InvalidCoSignData(f"Missing '{self.provides_auth}' parameter/value")
        return {
            "identifier": claim,
            "fields": {},
        }

    def add_claims_to_sessions_if_not_cosigning(self, claim, request):
        # set the session auth key only if we're not co-signing
        if claim and CO_SIGN_PARAMETER not in request.GET:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": self.identifier,
                "attribute": self.provides_auth,
                "value": claim,
            }

    def handle_return(self, request, form):
        """
        Redirect to form URL.
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        claim = request.session.get(self.session_key)

        self.add_claims_to_sessions_if_not_cosigning(claim, request)

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        if "oidc_id_token" in request.session:
            logout_endpoint = self.config_class.get_solo().oidc_op_logout_endpoint
            if logout_endpoint:
                logout_url = furl(logout_endpoint).set(
                    {
                        "id_token_hint": request.session["oidc_id_token"],
                    }
                )
                requests.get(str(logout_url))

            del request.session["oidc_id_token"]

        if "oidc_login_next" in request.session:
            del request.session["oidc_login_next"]

        if self.session_key in request.session:
            del request.session[self.session_key]


@register("digid_oidc")
class DigiDOIDCAuthentication(OIDCAuthentication):
    verbose_name = _("DigiD via OpenID Connect")
    provides_auth = AuthAttribute.bsn
    session_key = DIGID_OIDC_AUTH_SESSION_KEY
    claim_name = ""
    config_class = OpenIDConnectPublicConfig
    init_view = staticmethod(digid_init)

    def get_label(self) -> str:
        return "DigiD"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))


@register("eherkenning_oidc")
class eHerkenningOIDCAuthentication(OIDCAuthentication):
    verbose_name = _("eHerkenning via OpenID Connect")
    provides_auth = AuthAttribute.kvk
    session_key = EHERKENNING_OIDC_AUTH_SESSION_KEY
    claim_name = "kvk"
    config_class = OpenIDConnectEHerkenningConfig
    init_view = staticmethod(eherkenning_init)

    def get_label(self) -> str:
        return "eHerkenning"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))


@register("digid_machtigen_oidc")
class DigiDMachtigenOIDCAuthentication(OIDCAuthentication):
    verbose_name = _("DigiD Machtigen via OpenID Connect")
    provides_auth = AuthAttribute.bsn
    session_key = DIGID_MACHTIGEN_OIDC_AUTH_SESSION_KEY
    config_class = OpenIDConnectDigiDMachtigenConfig
    init_view = staticmethod(digid_machtigen_init)
    is_for_gemachtigde = True

    def add_claims_to_sessions_if_not_cosigning(self, claim, request):
        # set the session auth key only if we're not co-signing
        if not claim or CO_SIGN_PARAMETER in request.GET:
            return

        config = self.config_class.get_solo()
        machtigen_data = request.session[self.session_key]
        request.session[FORM_AUTH_SESSION_KEY] = {
            "plugin": self.identifier,
            "attribute": self.provides_auth,
            "value": claim[config.vertegenwoordigde_claim_name],
            "machtigen": {
                "identifier_value": machtigen_data.get(config.gemachtigde_claim_name)
            },
        }

    def get_label(self) -> str:
        return "DigiD Machtigen"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))


@register("eherkenning_bewindvoering_oidc")
class EHerkenningBewindvoeringOIDCAuthentication(OIDCAuthentication):
    verbose_name = _("eHerkenning bewindvoering via OpenID Connect")
    provides_auth = AuthAttribute.kvk
    session_key = EHERKENNING_BEWINDVOERING_OIDC_AUTH_SESSION_KEY
    config_class = OpenIDConnectEHerkenningBewindvoeringConfig
    init_view = staticmethod(eherkenning_bewindvoering_init)
    is_for_gemachtigde = True

    def add_claims_to_sessions_if_not_cosigning(self, claim, request):
        # set the session auth key only if we're not co-signing
        if not claim or CO_SIGN_PARAMETER in request.GET:
            return

        config = self.config_class.get_solo()
        machtigen_data = request.session[self.session_key]
        request.session[FORM_AUTH_SESSION_KEY] = {
            "plugin": self.identifier,
            "attribute": self.provides_auth,
            "value": claim[config.vertegenwoordigde_company_claim_name],
            "machtigen": {
                # TODO So far the only possibility is that this is a BSN.
                "identifier_value": machtigen_data.get(
                    config.gemachtigde_person_claim_name
                )
            },
        }

    def get_label(self) -> str:
        return "eHerkenning bewindvoering"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))
