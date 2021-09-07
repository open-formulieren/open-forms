from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.saml2.eherkenning import eHerkenningClient
from digid_eherkenning.views import (
    eHerkenningAssertionConsumerServiceView as _eHerkenningAssertionConsumerServiceView,
)
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

from openforms.authentication.contrib.digid.mixins import AssertionConsumerServiceMixin


class KVKNotPresentError(Exception):
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
            "eIDAS_no_kvk": _(
                "Login failed due to no KvK number being returned by eIDAS."
            )
        },
    )

    def get(self, request):
        saml_art = request.GET.get("SAMLart")

        client = eHerkenningClient()
        try:
            response = client.artifact_resolve(request, saml_art)
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
        except OneLogin_Saml2_ValidationError as exc:
            failure_url = self.get_failure_url(
                EIDAS_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
            )
            return HttpResponseRedirect(failure_url)

        kvk = None
        for attribute_value in attributes["urn:etoegang:core:LegalSubjectID"]:
            if not isinstance(attribute_value, dict):
                continue
            name_id = attribute_value["NameID"]
            if (
                name_id
                and name_id["NameQualifier"]
                == "urn:etoegang:1.9:EntityConcernedID:KvKnr"
            ):
                kvk = name_id["value"]

        if not kvk:
            self.log_error(request, self.error_messages["eidas_no_kvk"])
            raise KVKNotPresentError

        request.session["kvk"] = kvk

        return HttpResponseRedirect(self.get_success_url())
