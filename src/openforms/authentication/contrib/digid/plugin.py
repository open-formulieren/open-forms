from typing import Any, Dict, Optional

from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from furl import furl
from rest_framework.reverse import reverse

from openforms.contrib.digid_eherkenning.utils import get_digid_logo
from openforms.forms.models import Form

from ...base import BasePlugin, LoginLogo
from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from ...registry import register
from .constants import DIGID_AUTH_SESSION_KEY


@register("digid")
class DigidAuthentication(BasePlugin):
    verbose_name = _("DigiD")
    provides_auth = AuthAttribute.bsn

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str
    ) -> HttpResponseRedirect:
        """Redirect to the /digid/login endpoint to start step 2 of the authentication

        https://www.logius.nl/sites/default/files/public/bestanden/diensten/DigiD/Koppelvlakspecificatie-SAML-DigiD.pdf
        """
        login_url = reverse("digid:login", request=request)

        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": "digid"},
        )
        # The return_url becomes the DigiD relay state - this is why we add the co-sign
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
        if not (bsn := request.session.get(DIGID_AUTH_SESSION_KEY)):
            raise InvalidCoSignData("Missing 'bsn' parameter/value")
        return {
            "identifier": bsn,
            "fields": {},
        }

    def handle_return(self, request, form):
        """Redirect to form URL.

        This is called after step 7 of the authentication is finished
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        # set by the view :class:`.views.DigiDAssertionConsumerServiceView` after
        # valid DigiD login
        bsn = request.session.get(DIGID_AUTH_SESSION_KEY)

        # set the session auth key only if we're not co-signing
        if bsn and CO_SIGN_PARAMETER not in request.GET:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": "digid",
                "attribute": AuthAttribute.bsn,
                "value": bsn,
            }

        return HttpResponseRedirect(form_url)

    def get_logo(self, request) -> Optional[LoginLogo]:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))
