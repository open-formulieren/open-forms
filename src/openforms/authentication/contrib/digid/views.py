from urllib.parse import urlparse

from django.http import HttpResponseRedirect
from django.urls import resolve, reverse

from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.choices import SectorType
from digid_eherkenning.saml2.digid import DigiDClient
from digid_eherkenning.views import (
    DigiDAssertionConsumerServiceView as _DigiDAssertionConsumerServiceView,
)
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

from openforms.authentication.constants import AuthAttribute


class BSNNotPresentError(Exception):
    pass


class DigiDAssertionConsumerServiceView(
    BaseSaml2Backend, _DigiDAssertionConsumerServiceView
):
    """Process step 5, 6 and 7 of the authentication

    This class overwrites the digid_eherkenning class, because we don't need to use the authentication backend.
    We just need to receive the BSN number.
    """

    def get_form_slug(self) -> str:
        form_url = self.get_success_url()
        form_path = urlparse(form_url).path
        match = resolve(form_path)

        return match.kwargs["slug"]

    def get(self, request):
        saml_art = request.GET.get("SAMLart")
        client = DigiDClient()

        try:
            response = client.artifact_resolve(request, saml_art)
        except OneLogin_Saml2_ValidationError as exc:
            self.handle_validation_error(request)
            raise exc

        try:
            name_id = response.get_nameid()
        except OneLogin_Saml2_ValidationError as exc:
            self.handle_validation_error(request)
            raise exc

        sector_code, sectoral_number = name_id.split(":")

        # We only care about users with a BSN.
        if sector_code != SectorType.bsn:
            raise BSNNotPresentError

        bsn = sectoral_number
        request.session[AuthAttribute.bsn] = bsn

        # This is the URL of the form for which we are authenticating
        form_url = self.get_success_url()
        auth_plugin_url = reverse(
            "authentication:return",
            kwargs={"slug": self.get_form_slug(), "plugin_id": "digid"},
        )

        return HttpResponseRedirect(f"{auth_plugin_url}?next={form_url}")
