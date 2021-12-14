import logging
import time

from django.core.exceptions import DisallowedRedirect
from django.http import HttpResponseRedirect

import requests
from furl import furl
from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
    get_next_url,
)

from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .mixins import SoloConfigMixin

logger = logging.getLogger(__name__)


class OIDCAuthenticationRequestView(SoloConfigMixin, _OIDCAuthenticationRequestView):
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
                {"plugin_id": "eherkenning_oidc"},
                exc_info=e,
            )
            # append failure parameter and return to form
            f = furl(next_url)
            failure_url = f.args["next"]

            f = furl(failure_url)
            f.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = "eherkenning_oidc"
            return HttpResponseRedirect(f.url)

        return super().get(request)

    def get_extra_params(self, request):
        kc_idp_hint = self.get_settings("OIDC_KEYCLOAK_IDP_HINT", "")
        if kc_idp_hint:
            return {"kc_idp_hint": kc_idp_hint}
        return {}


class OIDCAuthenticationCallbackView(SoloConfigMixin, _OIDCAuthenticationCallbackView):
    def login_success(self):
        """
        Overridden to not actually log the user in, since setting the KVK number
        in the session variables is all that matters
        """

        # Figure out when this id_token will expire. This is ignored unless you're
        # using the RenewIDToken middleware.
        expiration_interval = self.get_settings(
            "OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS", 60 * 15
        )
        self.request.session["oidc_id_token_expiration"] = (
            time.time() + expiration_interval
        )

        return HttpResponseRedirect(self.success_url)
