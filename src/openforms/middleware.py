from datetime import timedelta

from django.middleware.csrf import get_token

from openforms.config.models import GlobalConfiguration

SESSION_EXPIRES_IN_HEADER = "X-Session-Expires-In"
CSRF_TOKEN_HEADER_NAME = "X-CSRFToken"


class SessionTimeoutMiddleware:
    """
    Allows us to set the expiry time of the session based on what
    is configured in our GlobalConfiguration
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        config = GlobalConfiguration.get_solo()
        timeout = (
            config.admin_session_timeout
            if request.user.is_staff
            else config.form_session_timeout
        )
        # https://docs.djangoproject.com/en/2.2/topics/http/sessions/#django.contrib.sessions.backends.base.SessionBase.set_expiry
        expires_in = int(timedelta(minutes=timeout).total_seconds())
        request.session.set_expiry(expires_in)
        response = self.get_response(request)
        response[SESSION_EXPIRES_IN_HEADER] = expires_in
        return response


class CsrfTokenMiddleware:
    """
    Add a CSRF Token to a response header
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only add the CSRF token header if it's an api endpoint
        if not request.path.startswith("/api"):
            return response

        response[CSRF_TOKEN_HEADER_NAME] = get_token(request)
        return response
