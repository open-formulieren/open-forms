import logging
from typing import Dict

from django.http import HttpResponseRedirect
from django.urls import resolve
from django.utils.translation import ugettext as _

from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.saml2.eherkenning import eHerkenningClient
from digid_eherkenning.views import (
    eHerkenningAssertionConsumerServiceView as _eHerkenningAssertionConsumerServiceView,
)
from furl import furl
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

from ...constants import FORM_AUTH_SESSION_KEY, AuthAttribute
from ..digid.mixins import AssertionConsumerServiceMixin

logger = logging.getLogger(__name__)


class ExpectedIdNotPresentError(Exception):
    pass


MESSAGE_PARAMETER = "_%(plugin_id)s-message"
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
            "missing_attribute": _(
                "Login failed due to no KvK number/Pseudo ID being returned by eHerkenning/eIDAS."
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
            if expected_id not in attributes:
                continue

            subjects = attributes[expected_id]
            for subject in subjects:
                qualifier_name = subject["NameID"]["NameQualifier"]
                qualifiers[qualifier_name] = subject["NameID"]["value"]

        return qualifiers

    def _get_plugin_id(self):
        redirect_url = self.get_redirect_url()
        url = resolve(furl(redirect_url).pathstr)
        return url.kwargs["plugin_id"]

    def get(self, request):
        """
        This view handles both the return from eHerkenning and eIDAS.
        """
        saml_art = request.GET.get("SAMLart")
        plugin_id = self._get_plugin_id()

        client = eHerkenningClient()
        try:
            response = client.artifact_resolve(request, saml_art)
            logger.debug(response.pretty_print())
        except OneLogin_Saml2_ValidationError as exc:
            if exc.code == OneLogin_Saml2_ValidationError.STATUS_CODE_AUTHNFAILED:
                failure_url = self.get_failure_url(
                    MESSAGE_PARAMETER % {"plugin_id": plugin_id}, LOGIN_CANCELLED
                )
            else:
                logger.error(exc)
                failure_url = self.get_failure_url(
                    MESSAGE_PARAMETER % {"plugin_id": plugin_id}, GENERIC_LOGIN_ERROR
                )
            return HttpResponseRedirect(failure_url)

        try:
            attributes = response.get_attributes()
        except OneLogin_Saml2_ValidationError as exc:
            logger.error(exc)
            failure_url = self.get_failure_url(
                MESSAGE_PARAMETER % {"plugin_id": plugin_id}, GENERIC_LOGIN_ERROR
            )
            return HttpResponseRedirect(failure_url)

        qualifiers = self._extract_qualifiers(attributes)

        if not qualifiers:
            self.log_error(request, self.error_messages["missing_attribute"])
            raise ExpectedIdNotPresentError

        if "urn:etoegang:1.9:EntityConcernedID:KvKnr" in qualifiers:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": plugin_id,
                "attribute": AuthAttribute.kvk,
                "value": qualifiers["urn:etoegang:1.9:EntityConcernedID:KvKnr"],
            }
        if "urn:etoegang:1.9:EntityConcernedID:Pseudo" in qualifiers:
            request.session[FORM_AUTH_SESSION_KEY] = {
                "plugin": plugin_id,
                "attribute": AuthAttribute.pseudo,
                "value": qualifiers["urn:etoegang:1.9:EntityConcernedID:Pseudo"],
            }

        return HttpResponseRedirect(self.get_success_url())
