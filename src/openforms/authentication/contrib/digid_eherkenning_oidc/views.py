import logging

from django.core.exceptions import DisallowedRedirect
from django.http import HttpResponseRedirect

import requests
from furl import furl
from mozilla_django_oidc.views import get_next_url

from digid_eherkenning_oidc_generics.mixins import (
    SoloConfigDigiDMixin,
    SoloConfigEHerkenningMixin,
)
from digid_eherkenning_oidc_generics.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
)

from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .backends import (
    OIDCAuthenticationDigiDBackend,
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


class DigiDOIDCAuthenticationRequestView(
    SoloConfigDigiDMixin, OIDCAuthenticationRequestView
):
    plugin_identifier = "digid_oidc"


class DigiDOIDCAuthenticationCallbackView(
    SoloConfigDigiDMixin, OIDCAuthenticationCallbackView
):
    auth_backend_class = OIDCAuthenticationDigiDBackend


class eHerkenningOIDCAuthenticationRequestView(
    SoloConfigEHerkenningMixin, OIDCAuthenticationRequestView
):
    plugin_identifier = "eherkenning_oidc"


class eHerkenningOIDCAuthenticationCallbackView(
    SoloConfigEHerkenningMixin, OIDCAuthenticationCallbackView
):
    auth_backend_class = OIDCAuthenticationEHerkenningBackend
