import time

from django.core.exceptions import DisallowedRedirect
from django.http import HttpResponseRedirect

from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
    get_next_url,
)

from .mixins import SoloConfigMixin


class OIDCAuthenticationRequestView(SoloConfigMixin, _OIDCAuthenticationRequestView):
    def get(self, request):
        redirect_field_name = self.get_settings("OIDC_REDIRECT_FIELD_NAME", "next")
        next_url = get_next_url(request, redirect_field_name)
        if not next_url:
            raise DisallowedRedirect

        return super().get(request)


class OIDCAuthenticationCallbackView(SoloConfigMixin, _OIDCAuthenticationCallbackView):
    def login_success(self):
        """
        Overridden to not actually log the user in, since setting the BSN in
        the session variables is all that matters
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
