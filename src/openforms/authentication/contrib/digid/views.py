from django.http import HttpResponseRedirect

from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.choices import SectorType
from digid_eherkenning.saml2.digid import DigiDClient
from digid_eherkenning.views import (
    DigiDAssertionConsumerServiceView as _DigiDAssertionConsumerServiceView,
)
from furl import furl
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.views import BACKEND_OUTAGE_RESPONSE_PARAMETER


class BSNNotPresentError(Exception):
    pass


class DigiDAssertionConsumerServiceView(
    BaseSaml2Backend,
    _DigiDAssertionConsumerServiceView,
):
    """Process step 5, 6 and 7 of the authentication

    This class overwrites the digid_eherkenning class, because we don't need to use the authentication backend.
    We just need to receive the BSN number.
    """

    def get_failure_url(self) -> str:
        url = self.get_success_url()
        f = furl(url)
        f.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = "digid"
        return f.url

    def get(self, request):
        saml_art = request.GET.get("SAMLart")
        client = DigiDClient()

        try:
            response = client.artifact_resolve(request, saml_art)
        except OneLogin_Saml2_ValidationError as exc:
            super().handle_validation_error(request)
            failure_url = self.get_failure_url()
            return HttpResponseRedirect(failure_url)

        try:
            name_id = response.get_nameid()
        except OneLogin_Saml2_ValidationError as exc:
            super().handle_validation_error(request)
            failure_url = self.get_failure_url()
            return HttpResponseRedirect(failure_url)

        sector_code, sectoral_number = name_id.split(":")

        # We only care about users with a BSN.
        if sector_code != SectorType.bsn:
            raise BSNNotPresentError

        bsn = sectoral_number
        request.session[AuthAttribute.bsn] = bsn

        return HttpResponseRedirect(self.get_success_url())
