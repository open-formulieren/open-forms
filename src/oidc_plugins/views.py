from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponseRedirect

from furl import furl
from mozilla_django_oidc_db.config import lookup_config
from mozilla_django_oidc_db.registry import register as registry
from mozilla_django_oidc_db.views import (
    _RETURN_URL_SESSION_KEY,
    OIDCAuthenticationCallbackView as _OIDCAuthenticationCallbackView,
)


class OIDCAuthAnonUserCallbackView(_OIDCAuthenticationCallbackView):
    """
    We only want to perform the claim processing, no real user is expected to
    be returned from the authentication backend, and hence we also don't want to try
    to log in this dummy user (as in, set ``request.user`` to a django user
    instance).

    Note that we deliberately don't perform these changes in :meth:`get` (anymore),
    since we miss the upstream library changes/fixes when we make invasive changes.
    Instead, the authentication backend receives all the necessary information and *is*
    the right place to implement this logic.
    """
    user: AnonymousUser  # set on succesful auth/code exchange

    _redirect_next: str

    def login_success(self):
        """
        Overridden to not actually log the user in, since setting the BSN/KVK/... in
        the session variables is all that matters.
        """
        assert self.user

        return HttpResponseRedirect(self.success_url)

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
        configuration = lookup_config(self.request)
        plugin = registry[configuration.identifier]

        return plugin.get_error_messages()

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

anon_user_callback_view = OIDCAuthAnonUserCallbackView.as_view()