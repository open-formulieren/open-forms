from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext as _

from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.saml2.eherkenning import eHerkenningClient
from digid_eherkenning.views import (
    eHerkenningAssertionConsumerServiceView as _eHerkenningAssertionConsumerServiceView,
)
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError


class KVKNotPresentError(Exception):
    pass


class eHerkenningAssertionConsumerServiceView(
    BaseSaml2Backend,
    _eHerkenningAssertionConsumerServiceView,
):
    error_messages = dict(
        BaseSaml2Backend.error_messages,
        **{
            "eherkenning_no_kvk": _(
                "Login failed due to no KVK being returned by eHerkenning."
            )
        },
    )

    def get(self, request):
        saml_art = request.GET.get("SAMLart")

        client = eHerkenningClient()
        try:
            response = client.artifact_resolve(request, saml_art)
        except OneLogin_Saml2_ValidationError as exc:
            self.handle_validation_error(request)
            raise exc

        try:
            attributes = response.get_attributes()
        except OneLogin_Saml2_ValidationError as exc:
            self.handle_validation_error(request)
            raise exc

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

        if not kvk or kvk == "":
            self.log_error(request, self.error_messages["eherkenning_no_kvk"])
            raise KVKNotPresentError

        request.session["kvk"] = kvk

        return HttpResponseRedirect(self.get_success_url())
