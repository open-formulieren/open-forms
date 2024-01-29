import logging

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import resolve

from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.choices import SectorType
from digid_eherkenning.saml2.digid import DigiDClient
from digid_eherkenning.views import (
    DigiDAssertionConsumerServiceView as _DigiDAssertionConsumerServiceView,
    DigiDLoginView as _DigiDLoginView,
)
from furl import furl
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

from openforms.forms.models import Form

from .constants import (
    DIGID_AUTH_SESSION_AUTHN_CONTEXTS,
    DIGID_AUTH_SESSION_KEY,
    DIGID_DEFAULT_LOA,
    PLUGIN_ID,
)
from .mixins import AssertionConsumerServiceMixin

logger = logging.getLogger(__name__)


class BSNNotPresentError(Exception):
    pass


DIGID_MESSAGE_PARAMETER = "_digid-message"
LOGIN_CANCELLED = "login-cancelled"
GENERIC_LOGIN_ERROR = "error"


class DigiDLoginView(_DigiDLoginView):
    def get_level_of_assurance(self):
        # get the form_slug from /auth/{slug}/...?next=...
        return_path = furl(self.request.GET.get("next")).path
        _, _, kwargs = resolve(return_path)
        form = get_object_or_404(Form, slug=kwargs.get("slug"))

        loa = form.authentication_backend_options.get(PLUGIN_ID, {}).get("loa")
        return loa if loa else DIGID_DEFAULT_LOA


class DigiDAssertionConsumerServiceView(
    AssertionConsumerServiceMixin,
    BaseSaml2Backend,
    _DigiDAssertionConsumerServiceView,
):
    """Process step 5, 6 and 7 of the authentication

    This class overwrites the digid_eherkenning class, because we don't need to use the authentication backend.
    We just need to receive the BSN number.
    """

    def get(self, request):
        saml_art = request.GET.get("SAMLart")
        client = DigiDClient()

        try:
            response = client.artifact_resolve(request, saml_art)
            logger.debug(response.pretty_print())
        except OneLogin_Saml2_ValidationError as exc:
            if exc.code == OneLogin_Saml2_ValidationError.STATUS_CODE_AUTHNFAILED:
                failure_url = self.get_failure_url(
                    DIGID_MESSAGE_PARAMETER, LOGIN_CANCELLED
                )
            else:
                logger.error(exc, exc_info=exc)
                failure_url = self.get_failure_url(
                    DIGID_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
                )
            return HttpResponseRedirect(failure_url)

        try:
            name_id = response.get_nameid()
        except OneLogin_Saml2_ValidationError as exc:
            logger.error(exc, exc_info=exc)
            failure_url = self.get_failure_url(
                DIGID_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
            )
            return HttpResponseRedirect(failure_url)

        match name_id.split(":"):
            case [SectorType.bsn, bsn]:
                pass
            case [bsn]:
                # Sectorcode missing; assume BSN as SOFI aren't issued since
                # Aanpassingswet Brp in 2014
                pass
            case _:
                raise BSNNotPresentError()

        # store the bsn itself in the session, and let the plugin decide where
        # to persist it. This is an implementation detail for this specific plugin!
        request.session[DIGID_AUTH_SESSION_KEY] = bsn
        # store the authn contexts so the plugin can check persmission when
        # accessing/creating an object
        request.session[DIGID_AUTH_SESSION_AUTHN_CONTEXTS] = (
            response.get_authn_contexts()
        )

        return HttpResponseRedirect(self.get_success_url())
