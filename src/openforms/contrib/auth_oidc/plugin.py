from __future__ import annotations

from typing import ClassVar, Protocol, TypedDict

from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseBase,
    HttpResponseRedirect,
)

from digid_eherkenning.oidc.models.base import BaseConfig
from mozilla_django_oidc_db.utils import do_op_logout
from mozilla_django_oidc_db.views import _RETURN_URL_SESSION_KEY

from openforms.authentication.base import BasePlugin, CosignSlice
from openforms.authentication.constants import (
    CO_SIGN_PARAMETER,
    FORM_AUTH_SESSION_KEY,
    AuthAttribute,
)
from openforms.authentication.exceptions import InvalidCoSignData
from openforms.authentication.registry import register
from openforms.authentication.typing import FormAuth
from openforms.forms.models import Form
from openforms.typing import JSONObject, StrOrPromise
from openforms.utils.urls import reverse_plus

from .constants import OIDC_ID_TOKEN_SESSION_KEY


def get_config_to_plugin() -> dict[type[BaseConfig], OIDCAuthentication]:
    """
    Get the mapping of config class to plugin identifier from the registry.
    """
    return {
        plugin.config_class: plugin
        for plugin in register
        if isinstance(plugin, OIDCAuthentication)
    }


class OptionsT(TypedDict):
    pass


class AuthInit(Protocol):
    def __call__(
        self, request: HttpRequest, return_url: str, options: OptionsT, *args, **kwargs
    ) -> HttpResponseBase: ...


# can't bind T to JSONObject because TypedDict and dict[str, ...] are not considered
# assignable... :(
class OIDCAuthentication[T, OptionsT](BasePlugin[OptionsT]):
    verbose_name: StrOrPromise = ""
    provides_auth: AuthAttribute
    session_key: str = ""
    config_class: ClassVar[type[BaseConfig]]
    init_view: ClassVar[AuthInit]

    def start_login(self, request: HttpRequest, form: Form, form_url: str, options):
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
        response = self.init_view(request, return_url=return_url, options=options)
        assert isinstance(response, HttpResponseRedirect)
        return response

    def handle_co_sign(self, request: HttpRequest, form: Form) -> CosignSlice:
        if not (claim := request.session.get(self.session_key)):
            raise InvalidCoSignData(f"Missing '{self.provides_auth}' parameter/value")
        return {
            "identifier": claim,
            "fields": {},
        }

    def before_process_claims(self, config: BaseConfig, claims: JSONObject):
        pass

    def strict_mode(self, request: HttpRequest) -> bool:
        return False

    def transform_claims(self, options: OptionsT, normalized_claims: T) -> FormAuth:
        raise NotImplementedError("Subclasses must implement 'transform_claims'")

    def failure_url_error_message(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        """
        Return a tuple of the parameter type and the problem code.
        """
        raise NotImplementedError(
            "Subclasses must implement 'failure_url_error_message'"
        )

    def extract_additional_claims(
        self, options: OptionsT, claims: JSONObject
    ) -> JSONObject:
        return {}

    def handle_return(self, request: HttpRequest, form: Form, options):
        """
        Redirect to form URL.
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        normalized_claims: T | None = request.session.get(self.session_key)
        if normalized_claims and CO_SIGN_PARAMETER not in request.GET:
            form_auth = self.transform_claims(options, normalized_claims)
            request.session[FORM_AUTH_SESSION_KEY] = form_auth

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        if id_token := request.session.get(OIDC_ID_TOKEN_SESSION_KEY):
            config = self.config_class.get_solo()
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
