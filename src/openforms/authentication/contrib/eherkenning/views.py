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


class ExpectedIdNotPresentError(Exception):
    pass


EHERKENNING_MESSAGE_PARAMETER = "_eherkenning-message"
LOGIN_CANCELLED = "login-cancelled"
GENERIC_LOGIN_ERROR = "error"


class eHerkenningAssertionConsumerServiceView(
    AssertionConsumerServiceMixin,
    BaseSaml2Backend,
    _eHerkenningAssertionConsumerServiceView,
):
    error_messages = dict(
        BaseSaml2Backend.error_messages,
        **{
            "eherkenning_no_kvk": _(
                "Login failed due to no KvK number being returned by eHerkenning."
            )
        },
    )

    def _extract_qualifiers(self, attributes: dict) -> Dict[str, str]:
        qualifiers = {}
        expected_ids = [
            "urn:etoegang:core:ActingSubjectID",
            "urn:etoegang:core:LegalSubjectID",
        ]
        for expected_id in expected_ids:
            if not expected_id in attributes:
                continue

            subjects = attributes[expected_id]
            for subject in subjects:
                qualifier_name = subject["NameID"]["NameQualifier"]
                qualifiers[qualifier_name] = subject["NameID"]["value"]

        return qualifiers

    def get(self, request):
        saml_art = request.GET.get("SAMLart")

        client = eHerkenningClient()
        try:
            response = client.artifact_resolve(request, saml_art)
        except OneLogin_Saml2_ValidationError as exc:
            if exc.code == OneLogin_Saml2_ValidationError.STATUS_CODE_AUTHNFAILED:
                failure_url = self.get_failure_url(
                    EHERKENNING_MESSAGE_PARAMETER, LOGIN_CANCELLED
                )
            else:
                failure_url = self.get_failure_url(
                    EHERKENNING_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
                )
            return HttpResponseRedirect(failure_url)

        try:
            attributes = response.get_attributes()
        except OneLogin_Saml2_ValidationError as exc:
            failure_url = self.get_failure_url(
                EHERKENNING_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
            )
            return HttpResponseRedirect(failure_url)

        qualifiers = self._extract_qualifiers(attributes)

        if not qualifiers:
            self.log_error(request, self.error_messages["eherkenning_no_kvk"])
            raise ExpectedIdNotPresentError

        if "urn:etoegang:1.9:EntityConcernedID:KvKnr" in qualifiers:
            request.session["kvk"] = qualifiers[
                "urn:etoegang:1.9:EntityConcernedID:KvKnr"
            ]
        if "urn:etoegang:1.9:EntityConcernedID:Pseudo" in qualifiers:
            request.session["pseudo_id"] = qualifiers[
                "urn:etoegang:1.9:EntityConcernedID:Pseudo"
            ]

        return HttpResponseRedirect(self.get_success_url())
