from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from furl import furl
from rest_framework.reverse import reverse

from openforms.contrib.digid_eherkenning.utils import get_digid_logo
from openforms.forms.models import Form

from ...base import BasePlugin, CosignSlice, LoginLogo
from ...constants import CO_SIGN_PARAMETER, FORM_AUTH_SESSION_KEY, AuthAttribute
from ...exceptions import InvalidCoSignData
from ...registry import register


@register("digid-mock")
class DigidMockAuthentication(BasePlugin):
    verbose_name = _("DigiD Mock")
    provides_auth = (AuthAttribute.bsn,)
    is_demo_plugin = True

    def start_login(self, request: HttpRequest, form: Form, form_url: str, options):
        url = reverse("digid-mock:login", request=request)
        acs = furl(self.get_return_url(request, form))
        if co_sign_param := request.GET.get(CO_SIGN_PARAMETER):
            acs.args[CO_SIGN_PARAMETER] = co_sign_param
        params = {
            "acs": str(acs),
            "next": form_url,
            "cancel": form_url,
        }
        url = f"{url}?{urlencode(params)}"
        return HttpResponseRedirect(url)

    def handle_co_sign(self, request: HttpRequest, form: Form) -> CosignSlice:
        if not (bsn := request.GET.get("bsn")):
            raise InvalidCoSignData("Missing 'bsn' parameter/value")
        return {
            "identifier": bsn,
            "fields": {},
        }

    def handle_return(self, request, form, options):
        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        bsn = request.GET.get("bsn")
        if not bsn:
            return HttpResponseBadRequest("missing 'bsn' parameter")

        # set the session auth key only if we're not co-signing
        if CO_SIGN_PARAMETER not in request.GET:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": self.identifier,
                "attribute": self.provides_auth[0],
                "value": bsn,
            }

        return HttpResponseRedirect(form_url)

    def get_logo(self, request) -> LoginLogo | None:
        return LoginLogo(title=self.get_label(), **get_digid_logo(request))
