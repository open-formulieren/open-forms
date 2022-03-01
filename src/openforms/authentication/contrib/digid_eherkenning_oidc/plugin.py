from typing import Any, Dict, Optional

from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

import requests
from furl import furl
from rest_framework.reverse import reverse

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectEHerkenningConfig,
    OpenIDConnectPublicConfig,
)
from openforms.authentication.base import BasePlugin, LoginLogo
from openforms.contrib.digid.utils import get_digid_logo
from openforms.contrib.eherkenning.utils import get_eherkenning_logo
from openforms.forms.models import Form

from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from ...registry import register
from .constants import DIGID_OIDC_AUTH_SESSION_KEY, EHERKENNING_OIDC_AUTH_SESSION_KEY


class OIDCAuthentication(BasePlugin):
    verbose_name = ""
    provides_auth = ""
    init_url = ""
    session_key = ""
    config_class = None

    def start_login(self, request: HttpRequest, form: Form, form_url: str):
        login_url = reverse(self.init_url, request=request)

        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": self.identifier},
        )
        return_url = furl(auth_return_url).set(
            {
                "next": form_url,
            }
        )
        if co_sign_param := request.GET.get(CO_SIGN_PARAMETER):
            return_url.args[CO_SIGN_PARAMETER] = co_sign_param

        redirect_url = furl(login_url).set({"next": str(return_url)})
        return HttpResponseRedirect(str(redirect_url))

    def handle_co_sign(
        self, request: HttpRequest, form: Form
    ) -> Optional[Dict[str, Any]]:
        if not (claim := request.session.get(self.session_key)):
            raise InvalidCoSignData(f"Missing '{self.provides_auth}' parameter/value")
        return {
            "identifier": claim,
            "fields": {},
        }

    def handle_return(self, request, form):
        """
        Redirect to form URL.
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        claim = request.session.get(self.session_key)

        # set the session auth key only if we're not co-signing
        if claim and CO_SIGN_PARAMETER not in request.GET:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": self.identifier,
                "attribute": self.provides_auth,
                "value": claim,
            }

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        if "oidc_id_token" not in request.session:
            return

        logout_endpoint = self.config_class.get_solo().oidc_op_logout_endpoint
        if logout_endpoint:
            logout_url = furl(logout_endpoint).set(
                {
                    "id_token_hint": request.session["oidc_id_token"],
                }
            )
            requests.get(str(logout_url))


@register("digid_oidc")
class DigiDOIDCAuthentication(OIDCAuthentication):
    verbose_name = _("DigiD via OpenID Connect")
    provides_auth = AuthAttribute.bsn
    init_url = "digid_oidc:init"
    session_key = DIGID_OIDC_AUTH_SESSION_KEY
    claim_name = ""
    config_class = OpenIDConnectPublicConfig

    def get_label(self) -> str:
        return "DigiD"

    def get_logo(self, request) -> Optional[LoginLogo]:
        return get_digid_logo(request, self.get_label())


@register("eherkenning_oidc")
class eHerkenningOIDCAuthentication(OIDCAuthentication):
    verbose_name = _("eHerkenning via OpenID Connect")
    provides_auth = AuthAttribute.kvk
    init_url = "eherkenning_oidc:init"
    session_key = EHERKENNING_OIDC_AUTH_SESSION_KEY
    claim_name = "kvk"
    config_class = OpenIDConnectEHerkenningConfig

    def get_label(self) -> str:
        return "eHerkenning"

    def get_logo(self, request) -> Optional[LoginLogo]:
        return get_eherkenning_logo(request, self.get_label())
