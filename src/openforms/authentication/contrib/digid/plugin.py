from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from digid_eherkenning.choices import DigiDAssuranceLevels
from furl import furl
from rest_framework.reverse import reverse

from openforms.contrib.digid_eherkenning.utils import get_digid_logo
from openforms.forms.models import Form
from openforms.typing import AnyRequest

from ...base import BasePlugin, CosignSlice, LoginLogo
from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from ...registry import register
from .config import DigidOptions, DigidOptionsSerializer
from .constants import (
    DIGID_AUTH_SESSION_AUTHN_CONTEXTS,
    DIGID_AUTH_SESSION_KEY,
    DIGID_DEFAULT_LOA,
    PLUGIN_ID,
)

_LOA_ORDER = [loa.value for loa in DigiDAssuranceLevels]


def loa_order(loa: str) -> int:
    # higher are defined later in the enum
    return -1 if loa not in _LOA_ORDER else _LOA_ORDER.index(loa)


@register(PLUGIN_ID)
class DigidAuthentication(BasePlugin[DigidOptions]):
    verbose_name = _("DigiD")
    provides_auth = (AuthAttribute.bsn,)
    configuration_options = DigidOptionsSerializer

    def start_login(
        self, request: HttpRequest, form: Form, form_url: str, options: DigidOptions
    ) -> HttpResponseRedirect:
        """Redirect to the /digid/login endpoint to start step 2 of the authentication

        https://www.logius.nl/sites/default/files/public/bestanden/diensten/DigiD/Koppelvlakspecificatie-SAML-DigiD.pdf
        """
        login_url = reverse("digid:login", request=request)

        auth_return_url = reverse(
            "authentication:return",
            kwargs={"slug": form.slug, "plugin_id": PLUGIN_ID},
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

    def handle_co_sign(self, request: HttpRequest, form: Form) -> CosignSlice:
        if not (bsn := request.session.get(DIGID_AUTH_SESSION_KEY)):
            raise InvalidCoSignData("Missing 'bsn' parameter/value")
        return {
            "identifier": bsn,
            "fields": {},
        }

    def handle_return(self, request, form, options: DigidOptions):
        """Redirect to form URL.

        This is called after step 7 of the authentication is finished
        """
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        # set by the view :class:`.views.DigiDAssertionConsumerServiceView` after
        # valid DigiD login
        bsn = request.session.get(DIGID_AUTH_SESSION_KEY)
        authn_contexts = request.session.get(DIGID_AUTH_SESSION_AUTHN_CONTEXTS, [""])

        # set the session auth key only if we're not co-signing
        if bsn and CO_SIGN_PARAMETER not in request.GET:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": PLUGIN_ID,
                "attribute": AuthAttribute.bsn,
                "value": bsn,
                "loa": max(authn_contexts, key=loa_order),
            }

        return HttpResponseRedirect(form_url)

    def check_requirements(self, request: AnyRequest, options: DigidOptions) -> bool:
        # check LoA requirements
        authenticated_loa = request.session[FORM_AUTH_SESSION_KEY]["loa"]
        required = options["loa"] or DIGID_DEFAULT_LOA
        return loa_order(authenticated_loa) >= loa_order(required)

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=str(self.get_label()), **get_digid_logo(request))

    def logout(self, request: HttpRequest):
        if DIGID_AUTH_SESSION_KEY in request.session:
            del request.session[DIGID_AUTH_SESSION_KEY]
