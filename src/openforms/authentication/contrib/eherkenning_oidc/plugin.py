from typing import Any, Dict, Optional
from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

import requests
from furl import furl
from rest_framework.reverse import reverse

from openforms.authentication.base import BasePlugin, LoginLogo
from openforms.authentication.registry import register
from openforms.forms.models import Form

from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from .constants import EHERKENNING_OIDC_AUTH_SESSION_KEY
from .models import OpenIDConnectEHerkenningConfig


@register("eherkenning_oidc")
class eHerkenningOIDCAuthentication(BasePlugin):
    verbose_name = _("eHerkenning via OpenID Connect")
    provides_auth = AuthAttribute.kvk

    def start_login(self, request: HttpRequest, form: Form, form_url: str):
        login_url = reverse(
            "eherkenning_oidc:oidc_authentication_init", request=request
        )

        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "eherkenning_oidc"},
        )
        # The return_url becomes the eherkenning relay state - this is why we add the co-sign
        # param to that URL and not the `form_url`.
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
        if not (kvk := request.session.get(EHERKENNING_OIDC_AUTH_SESSION_KEY)):
            raise InvalidCoSignData("Missing 'kvk' parameter/value")
        return {
            "identifier": kvk,
            "fields": {},
        }

    def handle_return(self, request, form):
        """
        Redirect to form URL.
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        # set by the auth backend :class:`.views.OIDCAuthenticationeHerkenningBackend` after
        # valid eHerkenning login
        kvk = request.session.get(EHERKENNING_OIDC_AUTH_SESSION_KEY)

        # set the session auth key only if we're not co-signing
        if kvk and CO_SIGN_PARAMETER not in request.GET:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": "eherkenning_oidc",
                "attribute": AuthAttribute.kvk,
                "value": kvk,
            }

        return HttpResponseRedirect(form_url)

    def logout(self, request: HttpRequest):
        params = urlencode({"id_token_hint": request.session["oidc_id_token"]})
        logout_endpoint = (
            OpenIDConnectEHerkenningConfig.get_solo().oidc_op_logout_endpoint
        )
        requests.get(f"{logout_endpoint}?{params}")

    def get_label(self) -> str:
        return "eHerkenning"

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(
            title=self.get_label(),
            image_src=request.build_absolute_uri(static("img/eherkenning.svg")),
            href="https://www.eherkenning.nl/",
        )
