import logging
from typing import Any

from django.http import HttpResponseRedirect
from django.urls import resolve
from django.utils.translation import gettext as _

from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.saml2.eherkenning import eHerkenningClient
from digid_eherkenning.views import (
    eHerkenningAssertionConsumerServiceView as _eHerkenningAssertionConsumerServiceView,
)
from furl import furl
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

from ..digid.mixins import AssertionConsumerServiceMixin
from .constants import (
    EHERKENNING_AUTH_SESSION_AUTHN_CONTEXTS,
    EHERKENNING_AUTH_SESSION_KEY,
    EHERKENNING_BRANCH_NUMBERS_SESSION_KEY,
    EIDAS_AUTH_SESSION_KEY,
)

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

    def _extract_qualifiers(self, attributes: dict) -> dict[str, str]:
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

        def flatten(maybe_list: Any):
            "Flatten singleton list"
            match maybe_list:
                case [singleton]:
                    return singleton
                case _:
                    return maybe_list

        return (
            qualifiers if qualifiers else {a: flatten(v) for a, v in attributes.items()}
        )

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
            request.session[EHERKENNING_AUTH_SESSION_KEY] = qualifiers[
                "urn:etoegang:1.9:EntityConcernedID:KvKnr"
            ]

        if "urn:etoegang:1.9:EntityConcernedID:Pseudo" in qualifiers:
            request.session[EIDAS_AUTH_SESSION_KEY] = qualifiers[
                "urn:etoegang:1.9:EntityConcernedID:Pseudo"
            ]

        # Extract the branch number service restriction(s) - this is all super vague and
        # we don't seem to have proper test accounts for this...
        # See https://afsprakenstelsel.etoegang.nl/Startpagina/v2/interface-specifications-dv-hm,
        # section "AttributeStatement" for an example response.
        # This translates to a list of strings (12 chars, all digits)
        if branch_numbers := attributes.get(
            "urn:etoegang:1.9:ServiceRestriction:Vestigingsnr"
        ):
            logger.info("Got branch numbers: %r", branch_numbers)
            request.session[EHERKENNING_BRANCH_NUMBERS_SESSION_KEY] = branch_numbers

        # store the authn contexts so the plugin can check persmission when
        # accessing/creating an object
        request.session[EHERKENNING_AUTH_SESSION_AUTHN_CONTEXTS] = (
            response.get_authn_contexts()
        )
        return HttpResponseRedirect(self.get_success_url())
