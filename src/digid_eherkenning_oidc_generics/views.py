import logging
import time
from typing import Generic, TypeVar, cast

from django.contrib import auth
from django.core.exceptions import DisallowedRedirect, SuspiciousOperation
from django.http import HttpRequest, HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme

import requests
from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView as _OIDCAuthenticationRequestView,
)

from .exceptions import OIDCProviderOutage
from .models import (
    OpenIDConnectBaseConfig,
    OpenIDConnectDigiDMachtigenConfig,
    OpenIDConnectEHerkenningBewindvoeringConfig,
    OpenIDConnectEHerkenningConfig,
    OpenIDConnectPublicConfig,
)
from .utils import get_setting_from_config

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=OpenIDConnectBaseConfig)


class OIDCInit(Generic[T], _OIDCAuthenticationRequestView):
    """
    A 'view' to start an OIDC authentication flow.

    This view class is parametrized with the config model/class to retrieve the
    specific configuration, such as the identity provider endpoint to redirect the
    user to.

    This view is not necessarily meant to be exposed directly via a URL pattern, but
    rather specific views are to be created from it, e.g.:

    .. code-block:: python

        >>> digid_init = OIDCInit.as_view(config_class=OpenIDConnectPublicConfig)
        >>> redirect_response = digid_init(request)
        # Redirect to some keycloak instance, for example.

    These concrete views are intended to be wrapped by your own views so that you can
    supply the ``return_url`` parameter:

    .. code-block:: python

        def my_digid_login(request):
            return digid_init(request, return_url=request.GET["next"])

    Compared to :class:`mozilla_django_oidc.views.OIDCAuthenticationRequestView`, some
    extra actions are performed:

    * Any Keycloak IdP hint is added, if configured
    * The ``return_url`` is validated against unsafe redirects
    * The availability of the identity provider endpoint is checked, if it's not
      available, the :class:`digid_eherkenning_oidc_generics.exceptions.OIDCProviderOutage`
      exception is raised. Note that your own code needs to handle this appropriately!
    """

    config_class: type[OpenIDConnectBaseConfig] = OpenIDConnectBaseConfig
    _config: T
    """
    The config model/class to get the endpoints/credentials from.

    Specify this as a kwarg in the ``as_view(config_class=...)`` class method.
    """

    def get_settings(self, attr, *args):  # type: ignore
        if (config := getattr(self, "_config", None)) is None:
            # django-solo and type checking is challenging, but a new release is on the
            # way and should fix that :fingers_crossed:
            config = cast(T, self.config_class.get_solo())
            self._config = config
        return get_setting_from_config(config, attr, *args)

    def get(
        self, request: HttpRequest, return_url: str = "", *args, **kwargs
    ) -> HttpResponseRedirect:
        if not return_url:
            raise ValueError("You must pass a return URL")

        url_is_safe = url_has_allowed_host_and_scheme(
            url=return_url,
            allowed_hosts=request.get_host(),
            require_https=request.is_secure(),
        )
        if not url_is_safe:
            raise DisallowedRedirect(f"Can't redirect to '{return_url}'")

        self._check_idp_availability()

        # We add our own key to keep track of the redirect URL. In the case of
        # authentication failure (or canceled logins), the session is cleared by the
        # upstream library, so in the callback view we store this URL so that we know
        # where to redirect with the error information.
        self.request.session["of_redirect_next"] = return_url

        response = super().get(request, *args, **kwargs)

        # mozilla-django-oidc grabs this from request.GET and since that is not mutable,
        # it's easiest to just override the session key with the correct value.
        request.session["oidc_login_next"] = return_url

        return response

    def _check_idp_availability(self) -> None:
        endpoint = self.OIDC_OP_AUTH_ENDPOINT
        try:
            # Verify that the identity provider endpoint can be reached. This is where
            # the user ultimately gets redirected to.
            response = requests.get(endpoint)
            if response.status_code > 400:
                response.raise_for_status()
        except requests.RequestException as exc:
            logger.info(
                "OIDC provider endpoint '%s' could not be retrieved",
                endpoint,
                exc_info=exc,
            )
            raise OIDCProviderOutage() from exc

    def get_extra_params(self, request: HttpRequest) -> dict[str, str]:
        """
        Add a keycloak identity provider hint if configured.
        """
        extra = super().get_extra_params(request)
        options = self.config_class._meta
        # Store which config class to use in the params so that the callback view can
        # extract this again.
        # TODO: verify this cannot be tampered with!
        extra["config"] = f"{options.app_label}.{options.object_name}"
        if kc_idp_hint := self.get_settings("OIDC_KEYCLOAK_IDP_HINT", ""):
            extra["kc_idp_hint"] = kc_idp_hint
        return extra


digid_init = OIDCInit.as_view(config_class=OpenIDConnectPublicConfig)
digid_machtigen_init = OIDCInit.as_view(config_class=OpenIDConnectDigiDMachtigenConfig)
eherkenning_init = OIDCInit.as_view(config_class=OpenIDConnectEHerkenningConfig)
eherkenning_bewindvoering_init = OIDCInit.as_view(
    config_class=OpenIDConnectEHerkenningBewindvoeringConfig
)


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

            # Delete the state entry also for failed authentication attempts
            # to prevent replay attacks.
            if (
                "state" in request.GET
                and "oidc_states" in request.session
                and request.GET["state"] in request.session["oidc_states"]
            ):  # pragma: no cover
                del request.session["oidc_states"][request.GET["state"]]
                request.session.save()

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
