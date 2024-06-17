from django.http import HttpRequest
from django.urls import reverse

from furl import furl
from mozilla_django_oidc_db.views import (
    _OIDC_ERROR_SESSION_KEY,
    _RETURN_URL_SESSION_KEY,
    AdminCallbackView,
)

from ...views import BACKEND_OUTAGE_RESPONSE_PARAMETER
from .plugin import PLUGIN_IDENTIFIER


class CallbackView(AdminCallbackView):
    """
    Apply the integrity error catching behaviour from AdminCallbackView.

    Potential integrity constraint errors are caught, and login failures redirect the
    user back to the public frontend (SDK).
    """

    _redirect_next: str

    def get(self, request: HttpRequest):
        # grab where the redirect next from the session and store it as a temporary
        # attribute. in the event that the failure url needs to be overridden, we
        # then have the value available even *after* mozilla_django_oidc has flushed
        # the session.
        self._redirect_next = request.session.get(_RETURN_URL_SESSION_KEY, "")
        return super().get(request)

    @property
    def failure_url(self) -> str:
        """
        On failure, redirect to the form with an appropriate error message.
        """
        # handle integrity and validation errors by redirecting the user to the admin
        # failure view.
        if _OIDC_ERROR_SESSION_KEY in self.request.session:
            return reverse("admin-oidc-error")

        # this is expected to be the auth plugin return url, set by the OIDCInit view
        plugin_return_url = furl(
            self._redirect_next or self.get_settings("LOGIN_REDIRECT_URL", "/")
        )
        # this URL is expected to have a ?next query param pointing back to the frontend
        # where the form is rendered/embedded
        _next = plugin_return_url.args["next"]
        assert isinstance(_next, str)
        form_url = furl(_next)
        form_url.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = PLUGIN_IDENTIFIER
        return form_url.url


callback_view = CallbackView.as_view()
