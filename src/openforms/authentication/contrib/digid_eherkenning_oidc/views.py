import logging

from django.core.exceptions import DisallowedRedirect
from django.http import HttpResponseRedirect

import requests
from furl import furl
from mozilla_django_oidc.views import get_next_url

from digid_eherkenning_oidc_generics.mixins import (
    SoloConfigDigiDMachtigenMixin,
    SoloConfigDigiDMixin,
    SoloConfigEHerkenningMixin,
)
from digid_eherkenning_oidc_generics.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
)

from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .backends import (
    OIDCAuthenticationDigiDBackend,
    OIDCAuthenticationDigiDMachtigenBackend,
    OIDCAuthenticationEHerkenningBackend,
)

logger = logging.getLogger(__name__)


class OIDCAuthenticationRequestView(_OIDCAuthenticationRequestView):
    plugin_identifier = ""

    def get(self, request):
        redirect_field_name = self.get_settings("OIDC_REDIRECT_FIELD_NAME", "next")
        next_url = get_next_url(request, redirect_field_name)
        if not next_url:
            raise DisallowedRedirect

        try:
            # Verify that the identity provider endpoint can be reached
            response = requests.head(self.OIDC_OP_AUTH_ENDPOINT)
            if response.status_code > 400:
                response.raise_for_status()
        except Exception as e:
            logger.exception(
                "authentication exception during 'start_login()' of plugin '%(plugin_id)s'",
                {"plugin_id": self.plugin_identifier},
                exc_info=e,
            )
            # append failure parameter and return to form
            f = furl(next_url)
            failure_url = f.args["next"]

            f = furl(failure_url)
            f.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = self.plugin_identifier
            return HttpResponseRedirect(f.url)

        return super().get(request)


class OIDCAuthenticationCallbackView(_OIDCAuthenticationCallbackView):
    @property
    def failure_url(self):
        """
        On failure, redirect to the form with an appropriate error message
        """
        f = furl(self.success_url)
        f = furl(f.args["next"])
        f.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = self.plugin_identifier
        return f.url


class DigiDOIDCAuthenticationRequestView(
    SoloConfigDigiDMixin, OIDCAuthenticationRequestView
):
    plugin_identifier = "digid_oidc"


class DigiDOIDCAuthenticationCallbackView(
    SoloConfigDigiDMixin, OIDCAuthenticationCallbackView
):
    plugin_identifier = "digid_oidc"
    auth_backend_class = OIDCAuthenticationDigiDBackend


class eHerkenningOIDCAuthenticationRequestView(
    SoloConfigEHerkenningMixin, OIDCAuthenticationRequestView
):
    plugin_identifier = "eherkenning_oidc"


class eHerkenningOIDCAuthenticationCallbackView(
    SoloConfigEHerkenningMixin, OIDCAuthenticationCallbackView
):
    plugin_identifier = "eherkenning_oidc"
    auth_backend_class = OIDCAuthenticationEHerkenningBackend


class DigiDMachtigenOIDCAuthenticationRequestView(
    SoloConfigDigiDMachtigenMixin, OIDCAuthenticationRequestView
):
    plugin_identifier = "digid_machtigen_oidc"


class DigiDMachtigenOIDCAuthenticationCallbackView(
    SoloConfigDigiDMachtigenMixin, OIDCAuthenticationCallbackView
):
    plugin_identifier = "digid_machtigen_oidc"
    auth_backend_class = OIDCAuthenticationDigiDMachtigenBackend
