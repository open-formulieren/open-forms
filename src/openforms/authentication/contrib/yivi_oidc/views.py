import logging

from digid_eherkenning.oidc.models import BaseConfig
from django.http import HttpRequest

from digid_eherkenning.oidc.views import (
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
)
from furl import furl
from mozilla_django_oidc_db.config import lookup_config
from mozilla_django_oidc_db.views import _RETURN_URL_SESSION_KEY

from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER

logger = logging.getLogger(__name__)

YIVI_MESSAGE_PARAMETER = "_yivi-message"
LOGIN_CANCELLED = "login-cancelled"

class OIDCAuthenticationCallbackView(_OIDCAuthenticationCallbackView):
    """
    Relay error messages back to the frontend.

    This custom callback view relays any failures back to the public frontend URL of the
    form by setting the appropriate outage parameter and/or message.
    """

    expect_django_user: bool = False  # do NOT create real Django users

    _redirect_next: str

    def get(self, request: HttpRequest):
        # grab where the redirect next from the session and store it as a temporary
        # attribute. in the event that the failure url needs to be overridden, we
        # then have the value available even *after* mozilla_django_oidc has flushed
        # the session.
        self._redirect_next = request.session.get(_RETURN_URL_SESSION_KEY, "")
        return super().get(request)

    def get_error_message_parameters(
        self, error: str, error_description: str
    ) -> tuple[str, str]:
        """
        Return a tuple of the parameter type and the problem code.
        """
        from .plugin import (
            get_config_to_plugin
        )

        config_to_plugin = get_config_to_plugin()
        config_class = lookup_config(self.request)
        assert issubclass(config_class, BaseConfig)
        plugin = config_to_plugin[config_class]

        match error, error_description:

            # @TODO set case and change return error_description
            case (
                "access_denied",
                "The user cancelled",
            ):
                return YIVI_MESSAGE_PARAMETER, LOGIN_CANCELLED

            case _:
                return BACKEND_OUTAGE_RESPONSE_PARAMETER, plugin.identifier

    @property
    def failure_url(self) -> str:
        """
        On failure, redirect to the form with an appropriate error message.
        """
        # this is expected to be the auth plugin return url, set by the OIDCInit view
        plugin_return_url = furl(
            self._redirect_next or self.get_settings("LOGIN_REDIRECT_URL", "/")
        )
        # this URL is expected to have a ?next query param pointing back to the frontend
        # where the form is rendered/embedded
        _next = plugin_return_url.args["next"]
        assert isinstance(_next, str)
        form_url = furl(_next)

        parameter, problem_code = self.get_error_message_parameters(
            error=self.request.GET.get("error", ""),
            error_description=self.request.GET.get("error_description", ""),
        )
        form_url.args[parameter] = problem_code
        return form_url.url

callback_view = OIDCAuthenticationCallbackView.as_view()
