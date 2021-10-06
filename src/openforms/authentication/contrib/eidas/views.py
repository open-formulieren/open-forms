import logging
from typing import Dict

from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.saml2.eherkenning import eHerkenningClient
from digid_eherkenning.views import (
    eHerkenningAssertionConsumerServiceView as _eHerkenningAssertionConsumerServiceView,
)
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

from openforms.authentication.contrib.digid.mixins import AssertionConsumerServiceMixin

logger = logging.getLogger(__name__)


class PseudoIDNotPresentError(Exception):
    pass


EIDAS_MESSAGE_PARAMETER = "_eidas-message"
LOGIN_CANCELLED = "login-cancelled"
GENERIC_LOGIN_ERROR = "error"


class EIDASAssertionConsumerServiceView(
    AssertionConsumerServiceMixin,
    BaseSaml2Backend,
    _eHerkenningAssertionConsumerServiceView,
):
    error_messages = dict(
        BaseSaml2Backend.error_messages,
        **{
            "eIDAS_no_pseudo_id": _(
                "Login failed due to no PseudoID being returned by eIDAS."
            )
        },
    )

    def _extract_qualifiers(self, attributes: dict) -> Dict[str, str]:
        subjects = attributes["urn:etoegang:core:ActingSubjectID"]
        qualifiers = {}
        for subject in subjects:
            qualifier_name = subject["NameID"]["NameQualifier"]
            logger.error(qualifier_name)
            logger.error(type(qualifier_name))
            qualifiers[qualifier_name] = subject["NameID"]["value"]

        return qualifiers

    def get(self, request):
        saml_art = request.GET.get("SAMLart")

        client = eHerkenningClient()
        try:
            response = client.artifact_resolve(request, saml_art)
            logger.error(getattr(response, "_artifact_response", None))
        except OneLogin_Saml2_ValidationError as exc:
            if exc.code == OneLogin_Saml2_ValidationError.STATUS_CODE_AUTHNFAILED:
                failure_url = self.get_failure_url(
                    EIDAS_MESSAGE_PARAMETER, LOGIN_CANCELLED
                )
            else:
                failure_url = self.get_failure_url(
                    EIDAS_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
                )
            return HttpResponseRedirect(failure_url)

        try:
            attributes = response.get_attributes()
            logger.error(attributes)
        except OneLogin_Saml2_ValidationError as exc:
            failure_url = self.get_failure_url(
                EIDAS_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
            )
            return HttpResponseRedirect(failure_url)

        qualifiers = self._extract_qualifiers(attributes)

        if not qualifiers["urn:etoegang:1.9:EntityConcernedID:Pseudo"]:
            self.log_error(request, self.error_messages["eidas_no_pseudo_id"])
            raise PseudoIDNotPresentError

        request.session["pseudo_id"] = qualifiers[
            "urn:etoegang:1.9:EntityConcernedID:Pseudo"
        ]

        return HttpResponseRedirect(self.get_success_url())
