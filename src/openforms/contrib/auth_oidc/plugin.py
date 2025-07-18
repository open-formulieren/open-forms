from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, Protocol, TypedDict

from django.http import (
    HttpRequest,
    HttpResponseBadRequest,
    HttpResponseBase,
    HttpResponseRedirect,
)

from mozilla_django_oidc_db.registry import register as oidc_registry
from mozilla_django_oidc_db.utils import do_op_logout
from mozilla_django_oidc_db.views import (
    _RETURN_URL_SESSION_KEY,
    OIDCAuthenticationRequestInitView,
)

from openforms.authentication.base import BasePlugin, CosignSlice
from openforms.authentication.constants import (
    CO_SIGN_PARAMETER,
    FORM_AUTH_SESSION_KEY,
    AuthAttribute,
)
from openforms.authentication.exceptions import InvalidCoSignData
from openforms.authentication.types import OIDCErrors
from openforms.authentication.typing import FormAuth
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from openforms.forms.models import Form
from openforms.typing import StrOrPromise
from openforms.utils.urls import reverse_plus

from .constants import OIDC_ID_TOKEN_SESSION_KEY


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
    provides_auth: ClassVar[Sequence[AuthAttribute]]
    oidc_plugin_identifier: ClassVar[str]

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str, options: OptionsT
    ) -> HttpResponseRedirect:
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

        # TODO: using self.init_view passes "self" as first argument, workaround
        init_view = OIDCAuthenticationRequestInitView.as_view(
            identifier=self.oidc_plugin_identifier,
            allow_next_from_query=False,
        )
        response = init_view(request, return_url=return_url)
        assert isinstance(response, HttpResponseRedirect)
        return response

    def handle_co_sign(self, request: HttpRequest, form: Form) -> CosignSlice:
        if not (claim := request.session.get(self.oidc_plugin_identifier)):
            raise InvalidCoSignData(f"Missing '{self.provides_auth}' parameter/value")
        return {
            "identifier": claim,
            "fields": {},
        }

    def transform_claims(self, normalized_claims: T) -> FormAuth:
        raise NotImplementedError("Subclasses must implement 'transform_claims'")

    def handle_return(self, request: HttpRequest, form: Form, options: OptionsT):
        """
        Redirect to form URL.
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        normalized_claims: T | None = request.session.get(self.oidc_plugin_identifier)
        if normalized_claims and CO_SIGN_PARAMETER not in request.GET:
            form_auth = self.transform_claims(normalized_claims)
            request.session[FORM_AUTH_SESSION_KEY] = form_auth

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        if id_token := request.session.get(OIDC_ID_TOKEN_SESSION_KEY):
            oidc_plugin = oidc_registry[self.oidc_plugin_identifier]
            config = oidc_plugin.get_config()

            do_op_logout(config, id_token)

        keys_to_delete = (
            "oidc_login_next",  # from upstream library
            self.oidc_plugin_identifier,
            _RETURN_URL_SESSION_KEY,
            OIDC_ID_TOKEN_SESSION_KEY,
        )
        for key in keys_to_delete:
            if key in request.session:
                del request.session[key]

    def get_error_message_parameters(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        """Return the message code and the error description for a failed login."""
        errors = self.get_error_codes()
        if (
            error == "access_denied"
            and error_description == "The user cancelled"
            and "access_denied" in errors
        ):
            return errors["access_denied"]
        return (BACKEND_OUTAGE_RESPONSE_PARAMETER, self.identifier)

    def get_error_codes(self) -> OIDCErrors:
        raise NotImplementedError("Subclasses must implement 'get_error_codes'")
