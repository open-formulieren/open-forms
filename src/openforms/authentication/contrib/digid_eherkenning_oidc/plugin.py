from __future__ import annotations

from typing import Any, ClassVar, Generic, Protocol, TypeVar

from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseBase,
    HttpResponseRedirect,
)
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.oidc.models import OpenIDConnectBaseConfig
from mozilla_django_oidc_db.utils import do_op_logout
from mozilla_django_oidc_db.views import _RETURN_URL_SESSION_KEY

from openforms.contrib.digid_eherkenning.utils import (
    get_digid_logo,
    get_eherkenning_logo,
)
from openforms.forms.models import Form
from openforms.typing import JSONObject, StrOrPromise
from openforms.utils.urls import reverse_plus

from ...base import BasePlugin, LoginLogo
from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from ...registry import register
from .models import (
    OFDigiDConfig,
    OFDigiDMachtigenConfig,
    OFEHerkenningBewindvoeringConfig,
    OFEHerkenningConfig,
)
from .views import (
    digid_init,
    digid_machtigen_init,
    eherkenning_bewindvoering_init,
    eherkenning_init,
)

OIDC_ID_TOKEN_SESSION_KEY = "oidc_id_token"


def get_config_to_plugin() -> dict[type[OpenIDConnectBaseConfig], OIDCAuthentication]:
    """
    Get the mapping of config class to plugin identifier from the registry.
    """
    return {
        plugin.config_class: plugin
        for plugin in register
        if isinstance(plugin, OIDCAuthentication)
    }


class AuthInit(Protocol):
    def __call__(
        self, request: HttpRequest, return_url: str, *args, **kwargs
    ) -> HttpResponseBase: ...


T = TypeVar("T", bound=str | JSONObject)


class OIDCAuthentication(Generic[T], BasePlugin):
    verbose_name: StrOrPromise = ""
    provides_auth: AuthAttribute
    session_key: str = ""
    config_class: ClassVar[type[OpenIDConnectBaseConfig]]
    init_view: ClassVar[AuthInit]

    def start_login(self, request: HttpRequest, form: Form, form_url: str):
        return_url_query = {"next": form_url}
        if co_sign_param := request.GET.get(CO_SIGN_PARAMETER):
            return_url_query[CO_SIGN_PARAMETER] = co_sign_param

        return_url = reverse_plus(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
            request=request,
            query=return_url_query,
        )

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
        response = self.init_view(request, return_url=return_url)
        assert isinstance(response, HttpResponseRedirect)
        return response

    def handle_co_sign(self, request: HttpRequest, form: Form) -> dict[str, Any]:
        if not (claim := request.session.get(self.session_key)):
            raise InvalidCoSignData(f"Missing '{self.provides_auth}' parameter/value")
        return {
            "identifier": claim,
            "fields": {},
        }

    def translate_auth_data(self, session_value: T) -> tuple[str, None | JSONObject]:
        assert isinstance(session_value, str)
        return session_value, None

    def handle_return(self, request: HttpRequest, form: Form):
        """
        Redirect to form URL.
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        session_value: T | None = request.session.get(self.session_key)
        if session_value and CO_SIGN_PARAMETER not in request.GET:
            auth_value, machtigen_data = self.translate_auth_data(session_value)
            _machtigen_data = {"machtigen": machtigen_data} if machtigen_data else {}
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": self.identifier,
                "attribute": self.provides_auth,
                "value": auth_value,
                **_machtigen_data,
            }

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        if id_token := request.session.get(OIDC_ID_TOKEN_SESSION_KEY):
            config = self.config_class.get_solo()
            assert isinstance(config, OpenIDConnectBaseConfig)
            do_op_logout(config, id_token)

        keys_to_delete = (
            "oidc_login_next",  # from upstream library
            self.session_key,
            _RETURN_URL_SESSION_KEY,
            OIDC_ID_TOKEN_SESSION_KEY,
        )
        for key in keys_to_delete:
            if key in request.session:
                del request.session[key]


@register("digid_oidc")
class DigiDOIDCAuthentication(OIDCAuthentication[str]):
    verbose_name = _("DigiD via OpenID Connect")
    provides_auth = AuthAttribute.bsn
    session_key = "digid_oidc:bsn"
    config_class = OFDigiDConfig
    init_view = staticmethod(digid_init)

    def get_label(self) -> str:
        return "DigiD"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))


@register("eherkenning_oidc")
class eHerkenningOIDCAuthentication(OIDCAuthentication[str]):
    verbose_name = _("eHerkenning via OpenID Connect")
    provides_auth = AuthAttribute.kvk
    session_key = "eherkenning_oidc:kvk"
    config_class = OFEHerkenningConfig
    init_view = staticmethod(eherkenning_init)

    def get_label(self) -> str:
        return "eHerkenning"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))


@register("digid_machtigen_oidc")
class DigiDMachtigenOIDCAuthentication(OIDCAuthentication[JSONObject]):
    verbose_name = _("DigiD Machtigen via OpenID Connect")
    provides_auth = AuthAttribute.bsn
    session_key = "digid_machtigen_oidc:machtigen"
    config_class = OFDigiDMachtigenConfig
    init_view = staticmethod(digid_machtigen_init)
    is_for_gemachtigde = True

    def translate_auth_data(self, session_value: JSONObject) -> tuple[str, JSONObject]:
        # these keys are set by the authentication backend
        bsn_vertegenwoordigde = session_value.get("representee")
        assert isinstance(bsn_vertegenwoordigde, str)
        bsn_gemachtigde = session_value.get("authorizee")
        assert isinstance(bsn_gemachtigde, str)

        return bsn_vertegenwoordigde, {"identifier_value": bsn_gemachtigde}

    def get_label(self) -> str:
        return "DigiD Machtigen"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))


@register("eherkenning_bewindvoering_oidc")
class EHerkenningBewindvoeringOIDCAuthentication(OIDCAuthentication[JSONObject]):
    verbose_name = _("eHerkenning bewindvoering via OpenID Connect")
    provides_auth = AuthAttribute.kvk
    session_key = "eherkenning_bewindvoering_oidc:machtigen"
    config_class = OFEHerkenningBewindvoeringConfig
    init_view = staticmethod(eherkenning_bewindvoering_init)
    is_for_gemachtigde = True

    def translate_auth_data(self, session_value: JSONObject) -> tuple[str, JSONObject]:
        # these keys are set by the authentication backend
        bsn_vertegenwoordigde = session_value.get("representee")
        assert isinstance(bsn_vertegenwoordigde, str)
        kvk_gemachtigde = session_value.get("authorizee_legal_subject")
        assert isinstance(kvk_gemachtigde, str)

        return bsn_vertegenwoordigde, {"identifier_value": kvk_gemachtigde}

    def get_label(self) -> str:
        return "eHerkenning bewindvoering"

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_eherkenning_logo(request))
