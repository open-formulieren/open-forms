import logging
import time

from django.contrib import auth
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseRedirect

from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
)

logger = logging.getLogger(__name__)


class OIDCAuthenticationRequestView(_OIDCAuthenticationRequestView):
    def get_extra_params(self, request):
        kc_idp_hint = self.get_settings("OIDC_KEYCLOAK_IDP_HINT", "")
        if kc_idp_hint:
            return {"kc_idp_hint": kc_idp_hint}
        return {}


class OIDCAuthenticationCallbackView(_OIDCAuthenticationCallbackView):
    auth_backend_class = None

    def get(self, request):
        """
        Callback handler for OIDC authorization code flow

        Copied from mozilla-django-oidc but modified to directly authenticate using
        the configured backend class, instead of using Django's default authentication
        mechanism. This removes the need to include these backends in `settings.AUTHENTICATION_BACKENDS`
        """

        if request.GET.get("error"):
            # Ouch! Something important failed.
            # Make sure the user doesn't get to continue to be logged in
            # otherwise the refresh middleware will force the user to
            # redirect to authorize again if the session refresh has
            # expired.
            if request.user.is_authenticated:
                auth.logout(request)
            assert not request.user.is_authenticated
        elif "code" in request.GET and "state" in request.GET:

            # Check instead of "oidc_state" check if the "oidc_states" session key exists!
            if "oidc_states" not in request.session:
                return self.login_failure()

            # State and Nonce are stored in the session "oidc_states" dictionary.
            # State is the key, the value is a dictionary with the Nonce in the "nonce" field.
            state = request.GET.get("state")
            if state not in request.session["oidc_states"]:
                msg = "OIDC callback state not found in session `oidc_states`!"
                raise SuspiciousOperation(msg)

            # Get the nonce from the dictionary for further processing and delete the entry to
            # prevent replay attacks.
            nonce = request.session["oidc_states"][state]["nonce"]
            del request.session["oidc_states"][state]

            # Authenticating is slow, so save the updated oidc_states.
            request.session.save()
            # Reset the session. This forces the session to get reloaded from the database after
            # fetching the token from the OpenID connect provider.
            # Without this step we would overwrite items that are being added/removed from the
            # session in parallel browser tabs.
            request.session = request.session.__class__(request.session.session_key)

            kwargs = {
                "request": request,
                "nonce": nonce,
            }
            self.user = self.auth_backend_class().authenticate(**kwargs)

            if self.user and self.user.is_active:
                return self.login_success()
        return self.login_failure()

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
