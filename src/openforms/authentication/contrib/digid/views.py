from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import resolve

import structlog
from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.choices import SectorType
from digid_eherkenning.saml2.digid import DigiDClient
from digid_eherkenning.views.digid import (
    DigiDAssertionConsumerServiceView as _DigiDAssertionConsumerServiceView,
    DigiDLoginView as _DigiDLoginView,
)
from furl import furl
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

from openforms.forms.models import Form, FormAuthenticationBackend

from .constants import (
    DIGID_AUTH_SESSION_AUTHN_CONTEXTS,
    DIGID_AUTH_SESSION_KEY,
    DIGID_DEFAULT_LOA,
    PLUGIN_ID,
)
from .mixins import AssertionConsumerServiceMixin

logger = structlog.stdlib.get_logger(__name__)


class BSNNotPresentError(Exception):
    pass


DIGID_MESSAGE_PARAMETER = "_digid-message"
LOGIN_CANCELLED = "login-cancelled"
GENERIC_LOGIN_ERROR = "error"


class DigiDLoginView(_DigiDLoginView):
    def get_level_of_assurance(self):
        # get the form_slug from /auth/{slug}/...?next=...
        next_param = self.request.GET.get("next", "")
        return_path = furl(next_param).path
        _, _, kwargs = resolve(str(return_path))
        form = get_object_or_404(Form, slug=kwargs.get("slug"))

        # called after AuthenticationStartView.get(), which already checks if there is an
        # FormAuthenticationBackend object for the plugin. Still, as this endpoint can be
        # targeted directly, we should still handle non-existing
        # FormAuthenticationBackend situations.
        try:
            auth_backend = form.auth_backends.get(backend=PLUGIN_ID)
            # the authentication backend options can be None as well, so make sure we
            # can safely access the loa key
            return (auth_backend.options or {}).get("loa") or DIGID_DEFAULT_LOA
        except FormAuthenticationBackend.DoesNotExist:
            raise SuspiciousOperation("plugin not allowed")


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
            logger.debug("saml_artifact_resolved", response=response.pretty_print())
        except OneLogin_Saml2_ValidationError as exc:
            if exc.code == OneLogin_Saml2_ValidationError.STATUS_CODE_AUTHNFAILED:
                failure_url = self.get_failure_url(
                    DIGID_MESSAGE_PARAMETER, LOGIN_CANCELLED
                )
            else:
                logger.error("artifact_resolution_failure", exc_info=exc)
                failure_url = self.get_failure_url(
                    DIGID_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
                )
            return HttpResponseRedirect(failure_url)

        try:
            name_id = response.get_nameid()
        except OneLogin_Saml2_ValidationError as exc:
            logger.error("name_id_extraction_failure", exc_info=exc)
            failure_url = self.get_failure_url(
                DIGID_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
            )
            return HttpResponseRedirect(failure_url)

        assert name_id is not None
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
        # store the authn contexts so the plugin can check permission when
        # accessing/creating an object
        request.session[DIGID_AUTH_SESSION_AUTHN_CONTEXTS] = (
            response.get_authn_contexts()
        )

        return HttpResponseRedirect(self.get_success_url())
